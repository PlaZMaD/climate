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


with_patch <- function(s4, closure_name, patched_closure, extra_args, code){
    # instead of original closure,
    # patched_closure(original_closure, extra_args, ...) will be called

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
	grepl('EProc$sEstUstarThold', err$call, fixed = TRUE) %>% any &&
		err$message == 'Missing columns in dataset: Rg'
}


get_ustar_daytime_arg <- function(rg_missing, default_arg, ustar_allow_skip_rg_filter) {
	if (!rg_missing)
		return(default_arg)

	if (ustar_allow_skip_rg_filter){
		warning(RE, RU, 'Rg is missing, uStar will be applied to both day and night')
		return(TRUE)
	} else {
		warning(RE, RU, 'Rg is missing, failure is expected during day/night detection when applying uStar.\n',
				'Consider enabling experimental option ustar_allow_skip_rg_filter.\n')
		return(default_arg)
	}
}


.ustar_threshold_fallback <- function(eddyProcConfiguration, EProc) {
    all_thresgolds_ok <- !anyNA(EProc$sUSTAR_SCEN$uStar)
    can_substitute_by_user_preset <- !is.na(eddyProcConfiguration$ustar_fallback_value)

    if (all_thresgolds_ok)
        return()

    if (!can_substitute_by_user_preset) {
        warning(RE, RU, 'option is NA, skipping user threshold.\n',
                'Fallback value is NaN. Gap fill failure is expected.\n')
        return()
    }

    before <- EProc$sUSTAR_SCEN
    EProc$sUSTAR_SCEN$uStar[is.na(EProc$sUSTAR_SCEN$uStar)] <- eddyProcConfiguration$ustar_fallback_value

    printed_df <- function(df)
        paste(capture.output(df), collapse = '\n')

    warning(RE, RU, 'Thresholds not for all seasons were calcualted automatically.\n',
            'Fallback value from the user options will be used. Before:\n',
            printed_df(before), '\nAfter: \n', printed_df(EProc$sUSTAR_SCEN))
}


.ustar_rg_safeguard <- function(estUStarThreshold_call, EProc) {
	season_guess <- function() {factor(levels(EProc$sTEMP$season))}

	# if Rg (solar radiation) is missing, still estimate season with NA u*
	tryCatch({

		estUStarThreshold_call()

		if (any(EProc$sUSTAR_SCEN$season != season_guess()))
			warning(RE, RU, 'unexpected seasons.\n',
					'Current run is ok, but workaround for seasons wont work on similar data. \n')
	}, error = function(err) {
		if (!is_error_ustar_need_rg(err))
			stop(err)

		p <- parent.env(environment())
		seasons_ok <- !is.null(p$EProc$sUSTAR_SCEN) && ncol(p$EProc$sUSTAR_SCEN) > 0
		assert(!seasons_ok)

		message(RE, RU, 'workaround for seasons detection will be applied')
		p$EProc$sUSTAR_SCEN <- data.frame(season = season_guess(), uStar = NA, row.names = NULL)
	})
}


est_ustar_threshold_fixes <- function(estUStarThreshold_call, eddyProcConfiguration, EProc) {
	.ustar_rg_safeguard(estUStarThreshold_call, EProc)
	.ustar_threshold_fallback(eddyProcConfiguration, EProc)
}
