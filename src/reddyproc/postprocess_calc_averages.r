library(dplyr)
library(lubridate)
library(tibble)

source('src/reddyproc/r_helpers.r')


.aggregate_df <- function(data, by_col, FUN) {
    # forms unique combinations with by_col
    # applies agg_FUN to all rows matching onr of combination
    # usually original dataframe is simply df = cbind(by_col, data)

    # rev(by_col): reverse is nessesary for YMD column order,
    # i.e. correct sort order during aggregate is 1) DoY 2) Month 3) Year
    res <- aggregate(data, by = rev(by_col), FUN = FUN)

    # restore YMD column order
    res <- res[c(colnames(by_col), colnames(data))]
    return(res)
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


.remove_too_short_years <- function(df) {
    stopifnot(nrow(df) > 3)

    first <- 1
    last <- nrow(df)

    if (df$Year[1] < df$Year[2]) {
        cat('Averages: first row excluded due to too short year \n')
        first <- 2
    }
    if (df$Year[nrow(df) - 1] < df$Year[nrow(df)]) {
        cat('Averages: last row excluded due to too short year \n')
        last <- nrow(df) - 1
    }

    df[first:last,]
}


calc_averages <- function(df_full){
    # save_reddyproc_df(df_full, 'test.csv')

    df <- .remove_too_short_years(df_full)
    df <- add_column(df, Month = month(df$DateTime), .after = 'Year')
    df <- add_column(df, DoM = day(df$DateTime), .after = 'Year')

    # indeed, R have no default list(str) better than %>% select
    cols_f <- colnames(df %>% select(ends_with("_f")))
    paired_cols_out <- setdiff(cols_f, 'GPP_f')
    paired_cols_in <- gsub("_f$", "", paired_cols_out)

    # additional optional mean columns
    extra_mean_cols <- intersect('Reco', colnames(df))
    # additional optional daily columns
    extra_daily_cols <- intersect('CH4flux', colnames(df))

    cols_to_mean <- c(cols_f, extra_mean_cols)
    cat('Columns picked for averaging (Reco added if possible): \n', cols_to_mean, '\n')

    cat('Columns picked for NA counts (GPP_f omitted): \n',paired_cols_in, '\n')

    missing = setdiff(paired_cols_in, colnames(df))
    if (length(missing) > 0)
        stop(msg = paste('Expected columns are missing: \n', missing, '\n'))

    df_to_mean <- df[cols_to_mean]
    df_to_nna <- df[paired_cols_in]

    # i.e. mean and NA percent will be calculated between rows
    # for which unique_cols values are matching, duplicates are ok
    unique_cols_d <- c('Year', 'Month', 'DoM', 'DoY')
    unique_cols_t <- c('Year', 'Month', 'Hour')
    unique_cols_m <- c('Year', 'Month')
    unique_cols_y <- c('Year')



    # hourly should also contain averages of columns before EProc
    df_to_mean_t <- cbind(df[cols_to_mean], df[paired_cols_in])
    # daily should also contain ch4 if avaliable
    df_to_mean_d <- cbind(df[cols_to_mean], df[extra_daily_cols])

    df_means_t <- .aggregate_df(df_to_mean_t, by_col = df[unique_cols_t], mean_nna)
    df_means_d <- .aggregate_df(df_to_mean_d, by_col = df[unique_cols_d], mean_nna)
    df_means_m <- .aggregate_df(df_to_mean, by_col = df[unique_cols_m], mean_nna)
    df_means_y <- .aggregate_df(df_to_mean, by_col = df[unique_cols_y], mean_nna)



    # renaming is easier before the actual calc
    cols_nna_sqc <- gsub("_f$", "_sqc", paired_cols_out)
    stopifnot(ncol(df_to_nna) == length(cols_nna_sqc) - length(missing))
    names(df_to_nna) <- cols_nna_sqc

    df_nna_t <- .aggregate_df(df_to_nna, by_col = df[unique_cols_t], nna_ratio)
    df_nna_d <- .aggregate_df(df_to_nna, by_col = df[unique_cols_d], nna_ratio)
    df_nna_m <- .aggregate_df(df_to_nna, by_col = df[unique_cols_m], nna_ratio)
    df_nna_y <- .aggregate_df(df_to_nna, by_col = df[unique_cols_y], nna_ratio)



    align_raw_sqc <- function(cn) gsub('*_sqc$', '', cn)
    df_t <- merge_cols_aligning(df_means_t, df_nna_t, unique_cols_t, align_raw_sqc)
    df_t <- add_column(df_t, ' ' = ' ', .after = tail(cols_to_mean, 1))

    align_f_sqc <- function(cn) gsub('*_sqc$', '_f', cn)
    df_d <- merge_cols_aligning(df_means_d, df_nna_d, unique_cols_d, align_f_sqc)
    df_m <- merge_cols_aligning(df_means_m, df_nna_m, unique_cols_m, align_f_sqc)
    df_y <- merge_cols_aligning(df_means_y, df_nna_y, unique_cols_y, align_f_sqc)

    # most of the ops will drop attrs, unit attrs must be restored back
    df_t <- .copy_attributes(df_t, df_full, 'units')
    df_d <- .copy_attributes(df_d, df_full, 'units')
    df_m <- .copy_attributes(df_m, df_full, 'units')
    df_y <- .copy_attributes(df_y, df_full, 'units')

    return(list(hourly = df_t, daily = df_d, monthly = df_m, yearly = df_y))
}


save_averages <- function(dfs, output_dir, output_unmask, ext){
    prename = file.path(output_dir, output_unmask)
    h_name <- paste0(prename, '_hourly', ext)
    d_name <- paste0(prename, '_daily', ext)
    m_name <- paste0(prename, '_monthly', ext)
    y_name <- paste0(prename, '_yearly', ext)

    dfs$hourly$Hour <- fmt_hm(dfs$hourly$Hour)

    write_with_units <- function(df, fname) {
        units_row <- as.character(lapply(df, attr, which = "units"))
        df <- insert_row(df, units_row, 1)
        write.csv(df, file = fname, row.names = FALSE, na = "-9999")
    }

    write_with_units(dfs$hourly, fname = h_name)
    write_with_units(dfs$daily, fname = d_name)
    write_with_units(dfs$monthly, fname = m_name)
    write_with_units(dfs$yearly, fname = y_name)

    cat(sprintf('Saved summary stats to : \n %s \n %s \n %s \n %s \n',
                d_name, m_name, y_name, h_name))

}
