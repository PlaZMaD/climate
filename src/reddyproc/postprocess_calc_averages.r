library(dplyr)
library(lubridate)
library(tibble)

source('src/reddyproc/r_helpers.r')
# TODO rename to postprocess_means


.aggregate_df <- function(data, by_col, FUN) {
    # forms unique combinations with by_col
    # applies agg_FUN to all rows matching onr of combination
    # usually original dataframe is simply df = cbind(by_col, data)

    # rev(by_col): reverse is nessesary for YMD column order,
    # i.e. correct sort order during aggregate is 1) DoY 2) Month 3) Year
    res <- aggregate(data, by = rev(by_col), FUN = FUN)

    # restore YMD column order
    res <- res[c(colnames(by_col), colnames(data))]
}


.copy_attributes <- function(df_target, df_source, attr_name) {
    same_cols <- intersect(colnames(df_target), colnames(df_source))
    for (col in same_cols)
        attr(df_target[,col], attr_name) <- attr(df_source[,col], attr_name)
    df_target
    # attr.names <- names(attributes(df_source))
    # attr.names <- attr.names[attr.names != 'names']
    # attributes(df_target)[attr.names] <- attributes(df_source)[attr.names]
}


.apply_attributes <- function(df, columns, attr_name, value) {
    for (col in columns)
        attr(df[,col], attr_name) <- value
    df
}


.remove_too_short_years <- function(df) {
    stopifnot(nrow(df) > 3)

    first <- 1
    last <- nrow(df)

    if (df$Year[1] < df$Year[2]) {
        cat(RM, 'First row excluded due to too short year \n')
        first <- 2
    }
    if (df$Year[nrow(df) - 1] < df$Year[nrow(df)]) {
        cat(RM, 'Last row excluded due to too short year \n')
        last <- nrow(df) - 1
    }

    df[first:last,]
}


.restore_unit_attributes <- function(df_h, df_d, df_m, df_y,
                                     unique_cols_h, unique_cols_d, unique_cols_m, unique_cols_y,
                                     df_full) {
    # most of the ops will drop attrs, unit attrs must be restored back
    # TODO or save them to list instead? but REddyProc stores in attrs
    df_h <- .copy_attributes(df_h, df_full, 'units')
    df_d <- .copy_attributes(df_d, df_full, 'units')
    df_m <- .copy_attributes(df_m, df_full, 'units')
    df_y <- .copy_attributes(df_y, df_full, 'units')

    df_h <- .apply_attributes(df_h, colnames(df_h %>% select(ends_with("_sqc"))), 'units', '--')
    df_d <- .apply_attributes(df_d, colnames(df_d %>% select(ends_with("_sqc"))), 'units', '--')
    df_m <- .apply_attributes(df_m, colnames(df_m %>% select(ends_with("_sqc"))), 'units', '--')
    df_y <- .apply_attributes(df_y, colnames(df_y %>% select(ends_with("_sqc"))), 'units', '--')

    df_h <- .apply_attributes(df_h, unique_cols_h, 'units', '--')
    df_d <- .apply_attributes(df_d, unique_cols_d, 'units', '--')
    df_m <- .apply_attributes(df_m, unique_cols_m, 'units', '--')
    df_y <- .apply_attributes(df_y, unique_cols_y, 'units', '--')

    list(h = df_h, d = df_d, m = df_m, y = df_y)
}


.get_gapfill_column_pairs <- function(df, known_unpaired_out) {
    # picks and checks REP gapfill column pairs:
    # if columns are
    # "DateTime" "Year" "DoM" ... "NEE" "LE" "Tair" "rH" ... "NEE_f" "LE_f" ...
    # then rreturns out columns: ["NEE_f", "LE_f"]
    # and corresponding in columns: ["NEE", "LE"]

    # indeed, R have no default list(str) better than %>% select
    cols_f <- colnames(df %>% select(ends_with("_f")))

    expected_cols_in <- sub("_f$", "", setdiff(cols_f, known_unpaired_out))
    cols_in = intersect(expected_cols_in, colnames(df))

    # TODO Bootstrap  -> NEE, GPP and Reco all into outputs
    missing_in = setdiff(expected_cols_in, cols_in)
    if (length(missing_in) > 0)
        stop(msg = paste('Expected columns are missing: \n', missing_in, '\n'))

    list(ins = cols_in, out = cols_f)
}


calc_averages <- function(df_full){
    # save_reddyproc_df(df_full, 'test.csv')

    df <- .remove_too_short_years(df_full)
    df <- add_column(df, Month = month(df$DateTime), .after = 'Year')
    df <- add_column(df, DoM = day(df$DateTime), .after = 'Year')

    known_unpaired_out <- c('NEE_U05_f', 'NEE_U50_f', 'NEE_U95_f',
                            'GPP_U05_f', 'GPP_U95_f', 'GPP_U50_f', 'GPP_f')
    col_pairs <- .get_gapfill_column_pairs(df, known_unpaired_out)


    # i.e. mean and NA percent will be calculated between rows
    # for which unique_cols values are matching, duplicates are ok
    unique_cols_d <- c('Year', 'Month', 'DoM', 'DoY')
    unique_cols_h <- c('Year', 'Month', 'Hour')
    unique_cols_m <- c('Year', 'Month')
    unique_cols_y <- c('Year')


    # additional optional mean columns
    extra_mean_cols <- intersect(c('GPP_DT', 'Reco', 'Reco_DT'), colnames(df))
    # additional optional hourly columns
    extra_cols_h <- intersect('CH4flux', colnames(df))

    cols_to_mean <- c(col_pairs$out, extra_mean_cols)
    cat(RM, 'Columns picked for means: \n', cols_to_mean, '\n')

    df_to_mean <- df[cols_to_mean]
    # hourly should also contain averages of columns before EProc and ch4 if avaliable
    df_to_mean_h <- df[c(cols_to_mean, col_pairs$ins, extra_cols_h)]

    df_means_h <- .aggregate_df(df_to_mean_h, by_col = df[unique_cols_h], mean_nna)
    df_means_d <- .aggregate_df(df_to_mean, by_col = df[unique_cols_d], mean_nna)
    df_means_m <- .aggregate_df(df_to_mean, by_col = df[unique_cols_m], mean_nna)
    df_means_y <- .aggregate_df(df_to_mean, by_col = df[unique_cols_y], mean_nna)


    cat(RM, 'Columns picked for NA counts: \n',col_pairs$ins , '\n')
    df_to_nna <- df[col_pairs$ins]
    df_to_nna_h <- df[c(col_pairs$ins,  extra_cols_h)]
    # renaming is easier before the actual calc
    names(df_to_nna) <- sub("$", "_sqc", names(df_to_nna))
    names(df_to_nna_h) <- sub("$", "_sqc", names(df_to_nna_h))

    df_nna_h <- .aggregate_df(df_to_nna_h, by_col = df[unique_cols_h], nna_ratio)
    df_nna_d <- .aggregate_df(df_to_nna, by_col = df[unique_cols_d], nna_ratio)
    df_nna_m <- .aggregate_df(df_to_nna, by_col = df[unique_cols_m], nna_ratio)
    df_nna_y <- .aggregate_df(df_to_nna, by_col = df[unique_cols_y], nna_ratio)



    align_raw_sqc <- function(cn) sub('*_sqc$', '', cn)
    df_h <- merge_cols_aligning(df_means_h, df_nna_h, unique_cols_h, align_raw_sqc)
    df_h <- add_column(df_h, ' ' = ' ', .after = tail(cols_to_mean, 1))

    align_f_sqc <- function(cn) sub('*_sqc$', '_f', cn)
    df_d <- merge_cols_aligning(df_means_d, df_nna_d, unique_cols_d, align_f_sqc)
    df_m <- merge_cols_aligning(df_means_m, df_nna_m, unique_cols_m, align_f_sqc)
    df_y <- merge_cols_aligning(df_means_y, df_nna_y, unique_cols_y, align_f_sqc)

    dfs <- .restore_unit_attributes(df_h, df_d, df_m, df_y,
                                    unique_cols_h, unique_cols_d, unique_cols_m, unique_cols_y,
                                    df_full)

    list(hourly = dfs$h, daily = dfs$d, monthly = dfs$m, yearly = dfs$y)
}


save_averages <- function(dfs, output_dir, output_unmask, ext){
    prename = file.path(output_dir, output_unmask)
    h_name <- paste0(prename, '_hourly', ext)
    d_name <- paste0(prename, '_daily', ext)
    m_name <- paste0(prename, '_monthly', ext)
    y_name <- paste0(prename, '_yearly', ext)

    bkp_attr <- attr(dfs$hourly$Hour, 'units')
    dfs$hourly$Hour <- fmt_hm(dfs$hourly$Hour)
    attr(dfs$hourly$Hour, 'units') <- bkp_attr


    write_with_units <- function(df, fname) {
        units_row <- sub('NULL$', '', as.character(lapply(df, attr, which = "units")))
        df <- insert_row(df, units_row, 1)
        write.csv(df, file = fname, row.names = FALSE, na = "-9999", quote = FALSE)
    }

    write_with_units(dfs$hourly, fname = h_name)
    write_with_units(dfs$daily, fname = d_name)
    write_with_units(dfs$monthly, fname = m_name)
    write_with_units(dfs$yearly, fname = y_name)

    cat(RM, sprintf('Saved summary stats to : \n %s \n %s \n %s \n %s \n',
                d_name, m_name, y_name, h_name))

}
