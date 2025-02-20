# TODO report bugfix
# daily sums plots of which variables rename to daily means
DAILY_SUMS_PLOT_TITLE_RENAMES = c('Tair_f', 'rH_f', 'Rg_f', 'H_f', 'LE_f', 'VPD_f')


DAILY_SUMS_UNITS = list(NEE_f = 'gC_m-2_day-1', NEE_uStar_f = 'gC_m-2_day-1',
                        LE_f = 'Wm-2', H_f = 'Wm-2', Rg_f = 'Wm-2',
                        Tair_f = 'degC', Tsoil_f = 'degC',
                        rH_f = '%', VPD_f = 'hPa', Ustar_f = 'ms-1', CH4flux_f = 'mg_m-2_day-1')


get_patched_daily_sum_unit <- function(eddyProcConfiguration, baseNameVal, table_unit){
    unit <- DAILY_SUMS_UNITS[[baseNameVal]]
    if (is.null(unit)){
        warning("\n\n Missing variable units for daily sums: ", baseNameVal,
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


# TODO does not work yet, should simplify patch_daily_sums_plot_name
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


.ustarThresholdFallback <- function(eddyProcConfiguration, EProc) {
    seasons_ok <- !is.null(EProc$sUSTAR_SCEN) && ncol(EProc$sUSTAR_SCEN) > 0
    all_thresgolds_ok <- !anyNA(EProc$sUSTAR_SCEN$uStar)
    can_substitute_by_user_preset <- !is.na(eddyProcConfiguration$ustar_fallback_value)
    season_guess <- factor(levels(EProc$sTEMP$season))


    if (seasons_ok && all_thresgolds_ok) {
        if (any(EProc$sUSTAR_SCEN$season != season_guess))
            warning('\n\n\nREddyProc uStar patch: unexpected seasons.\n',
                    'Current run is ok, but other runs with experimental seasons wont be. \n\n')
        return()
    }

    if (!can_substitute_by_user_preset) {
        warning('\n\nREddyProc uStar patch: option is NA, skipping user threshold.\n',
                'Fallback value is NaN. Gap fill failure is expected.\n')
        return()
    }

    if (!seasons_ok) {
        warning('\n\n\nREddyProc uStar patch: an attempt of  experimental seasons\n\n')
        EProc$sUSTAR_SCEN <- data.frame(season = season_guess, uStar = NA, row.names = NULL)
    }

    before <- EProc$sUSTAR_SCEN
    EProc$sUSTAR_SCEN$uStar[is.na(EProc$sUSTAR_SCEN$uStar)] <-
        eddyProcConfiguration$ustar_fallback_value

    printed_df <- function(df)
        paste(capture.output(df), collapse = '\n')

    warning('\n\nREddyProc uStar patch: filter have not automatically detected thresholds for some values.\n',
            'They were replaced with fixed fallback values. Before:\n',
            printed_df(before), '\nAfter: \n', printed_df(EProc$sUSTAR_SCEN), '\n')
}
