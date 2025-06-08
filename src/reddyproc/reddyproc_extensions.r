# TODO report bugfix to REP:
# daily sums plots should be named daily means for:
DAILY_SUMS_PLOT_TITLE_RENAMES = c('Tair_f', 'rH_f', 'Rg_f', 'H_f', 'LE_f', 'VPD_f')


DAILY_SUMS_UNITS = list(NEE_f = 'gC_m-2_day-1', NEE_uStar_f = 'gC_m-2_day-1',
                        LE_f = 'Wm-2', H_f = 'Wm-2', Rg_f = 'Wm-2',
                        Tair_f = 'degC', Tsoil_f = 'degC',
                        rH_f = '%', VPD_f = 'hPa', Ustar_f = 'ms-1', CH4flux_f = 'mg_m-2_day-1')


get_patched_daily_sum_unit <- function(eddyProcConfiguration, baseNameVal, table_unit){
    unit <- DAILY_SUMS_UNITS[[baseNameVal]]
    if (is.null(unit)){
        warning(RM, 'Missing variable units for daily sums: ', baseNameVal,
                "\nunit in the table: ", table_unit, ' daily sum unit: ', baseNameVal)
        return(table_unit)
    }
    return(unit)
}


patch_daily_sums_plot_name <- function(orig_call, var_name, ...) {
    title <- orig_call(...)
    if (var_name %in% DAILY_SUMS_PLOT_TITLE_RENAMES)
        title <- sub('Daily sums', 'Daily means', title)

    return(title)
}


with_patched_func <- function(s4, closure_name, patched_closure, extra_args, code = {}){
    # patches s4.closure_name with patched_closure(original_closure, extra_args, ...),
    # runs code,
	# ensures patch is removed after tha call

	code_str = substitute(code)
	if (!is.call(code_str))
		stop('with_patched_func code arg must be code block, not a bare function.',
			 'Correct example: with_patched_func(... , code = {function_to_call(...)}, ...)')

    original_closure <- s4[[closure_name]]
    tryCatch(
        expr = {
            s4[[closure_name]] <- function(...) {
                return(patched_closure(original_closure, extra_args, ...))
                }
            code
        },
        finally = {
            s4[[closure_name]] <- original_closure
        }
    )
}


is_error_ustar_need_rg <- function(err) {
	# TODO exact column name?
	grepl('EProc$sEstUstarThold', err$call, fixed = TRUE) %>% any &&
		err$message == 'Missing columns in dataset: '
}


check_ustar_daytime_arg <- function(real_rg_missing, eddyProcConfiguration) {
	epc <- eddyProcConfiguration

	if (real_rg_missing && epc$ustar_rg_source == 'Rg')
		warning(RE, RU, 'Missing Rg column is picked for day/night detection, ',
				'failure is expected when applying uStar.\n',
				' Consider changing option ustar_rg_source')

	if (epc$ustar_rg_source == '')
		warning(RE, RU, 'ustar_rg_source: uStar will be applied to both day and night, Rg ignored')
}


.ustar_threshold_fallback <- function(eddyProcConfiguration, EProc) {
    all_thresgolds_ok <- !anyNA(EProc$sUSTAR_SCEN$uStar)
    can_substitute_by_user_preset <- !is.na(eddyProcConfiguration$ustar_threshold_fallback)

    # TODO uncertanity?
    if (all_thresgolds_ok)
        return()
	message('\n', RE, RU, 'Thresholds not for all seasons were calculated automatically.')

    if (!can_substitute_by_user_preset) {
        warning(RE, RU, 'Fallback value is NaN, gap fill failure is expected.\n',
				'Consider changing ustar_threshold_fallback option\n')
        return()
    }

    before <- EProc$sUSTAR_SCEN
    EProc$sUSTAR_SCEN$uStar[is.na(EProc$sUSTAR_SCEN$uStar)] <- eddyProcConfiguration$ustar_threshold_fallback

    printed_df <- function(df)
        paste(capture.output(df), collapse = '\n')

    message(RE, RU, 'Fallback value from the user options will be used.\n',
			'Before:\n', printed_df(before), '\nAfter: \n', printed_df(EProc$sUSTAR_SCEN))
}


.verify_theoretical_rg <- function(rg_col, theor_col) {
	rg_nights <- rg_col < 10
	th_nights <- theor_col < 10

	nights_match = sum(rg_nights == th_nights, na.rm = TRUE)
	nights_match_ratio <- nights_match / sum(!is.na(rg_nights))
	nights_mismatch <- sum(rg_nights != th_nights, na.rm = TRUE)
	rg_missing_ratio <- sum(is.na(rg_nights)) / length(rg_col)

	abs_diff <- abs(rg_col - theor_col)
	mean_diff <- mean(abs_diff, na.rm = TRUE)
	median_diff <- median(abs_diff, na.rm = TRUE)

	fmt <- paste(' Both theoretical and real Rg columns are detected.',
				 ' Rg missing: %.2f%%',
				 ' Nights match: %.2f%%',
				 ' Mean theor vs real (when real is known): %.2f',
				 ' Median theor vs real (when real is known): %.2f', sep = '\n')
	message(RE, RU, sprintf(fmt, rg_missing_ratio * 100, nights_match_ratio * 100,
							mean_diff, median_diff))
}


.ustar_estimate_rg <- function(eddyProcConfiguration, EProc) {
	ep_cfg <- eddyProcConfiguration

	if (ep_cfg$ustar_rg_source == 'Rg_th_REP') {
		# TODO why 15, 45 mins when input file is 0, 30?
		hour_dec <- hour(EProc$sDATA$sDateTime) + minute(EProc$sDATA$sDateTime) / 60
		doy <- yday(EProc$sDATA$sDateTime)
		EProc$sDATA[[ep_cfg$ustar_rg_source]] <-
			fCalcPotRadiation(doy, hour_dec, ep_cfg$latitude, ep_cfg$longitude, ep_cfg$timezone)
	}

	if (ep_cfg$ustar_rg_source %in% c('Rg_th_REP', 'Rg_th_Py') && 'Rg' %in% colnames(EProc$sDATA))
		.verify_theoretical_rg(EProc$sDATA[['Rg']], EProc$sDATA[[ep_cfg$ustar_rg_source]])
}


.ustar_rg_safeguard <- function(estUStarThreshold_call, eddyProcConfiguration, EProc) {
	# if Rg (solar radiation) is missing, still estimate season with NA u*

	season_guess <- function() {factor(levels(EProc$sTEMP$season))}

	tryCatch({
		estUStarThreshold_call()

		if (any(EProc$sUSTAR_SCEN$season != season_guess()))
			warning(RE, RU, 'Not an error: unexpected seasons data detected.\n',
					'Please report data setup to improve support of Rg in the script. \n')
	}, error = function(err) {
		expected <- is_error_ustar_need_rg(err) && eddyProcConfiguration$ustar_rg_source == ''
		if (!expected)
			stop(err)

		p <- parent.env(environment())
		seasons_ok <- !is.null(p$EProc$sUSTAR_SCEN) && ncol(p$EProc$sUSTAR_SCEN) > 0
		assert(!seasons_ok)

		warning(RE, RU, 'Workaround for seasons detection will be applied. Seasons option ignored.')
		p$EProc$sUSTAR_SCEN <- data.frame(season = season_guess(), uStar = NA, row.names = NULL)
	})
}


est_ustar_threshold_fixes <- function(estUStarThreshold_call, eddyProcConfiguration, EProc) {
	.ustar_estimate_rg(eddyProcConfiguration, EProc)
	.ustar_rg_safeguard(estUStarThreshold_call, eddyProcConfiguration, EProc)
	.ustar_threshold_fallback(eddyProcConfiguration, EProc)
}
