EPROC_SX_SET_TITLE <- NULL

# TODO report bugfix
# daily sums plots of which variables rename to daily means
DAILY_SUMS_RENAMES = c('Rg', 'H', 'VPD')


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


set_title_patched <- function(...){
    title <- EPROC_SX_SET_TITLE(...)
    message('\n\n', title, '\n')

    return(title)
}
