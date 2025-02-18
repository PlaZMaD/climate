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

    title
}


# TODO does not work yet, should simplify patch_daily_sums_plot_name
with_patch <- function(s4, closure_name, patch, code){
    orig_method <- s4[[closure_name]]

    tryCatch(
        expr = {
            s4[[closure_name]] <- patch
            code
        },
        finally = {
            s4[[closure_name]] <- orig_method
        }
    )
}
