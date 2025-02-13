# common R routines, all in one file for now

library(dplyr)


is.not.null <- function(x) !is.null(x)
`%ni%` <- Negate(`%in%`)


assert <- function(x, msg){
    if (x != TRUE)
        stop('Assertion failure: ', msg)
}


.combine_cols_alternating <- function(df, df_add, expected_col_dupes){
    # not tested

    stopifnot(all(df[expected_col_dupes] == df_add[expected_col_dupes]))
    stopifnot(nrows(df) == nrows(df_add))

    df_ma <- df %>% select(-any_of(expected_col_dupes))
    df_mb <- df_add %>% select(-any_of(expected_col_dupes))

    neworder <- order(c(2 * (seq_along(df_ma) - 1) + 1,
                        2 * seq_along(df_mb)))

    merged_alternating <- cbind(df_ma, df_mb)[,neworder]
    cbind(df[expected_col_dupes], merged_alternating)
}


merge_cols_aligning <- function(df, df_add, expected_col_dupes, f_align_rule){
    # f_align_rule:
    #     function to propose best column insert position:
    #     function(<df_add_col_name>) -> <df_col_name>
    #     if returns NULL or df_column is missing, just adds df_add column to the right of df
    #
    #     for example, if f_align_rule is: function(cn) gsub('*_f$', '_sqc', cn)
    #     merge will be: H_f LE_f H_sqc LE_sqc -> H_f H_sqc U_f U_sqc LE_f LE_sqc

    stopifnot(df[expected_col_dupes] == df_add[expected_col_dupes])
    df_unique_add <- df_add %>% select(-matches(expected_col_dupes))

    colnames_df <- colnames(df)
    colnames_df_add <- colnames(df_unique_add)
    align_target <- f_align_rule(colnames_df_add)
    align_target[!align_target %in% colnames_df] <- NULL

    colnames_df_add_unpaired <- colnames_df_add[is.null(align_target)]

    col_or_paired <- function(cn) c(cn, colnames_df_add[align_target == cn])
    tgt_col_order <- c(unlist(Map(col_or_paired, colnames_df)), colnames_df_add_unpaired)

    df_res <- cbind(df, df_unique_add)

    stopifnot(ncol(tgt_col_order) == ncol(df_res))
    stopifnot(tgt_col_order %in% colnames(df_res) %>% all)

    return(df_res[tgt_col_order])
}


first_and_last <- function(vec){
    ret <- vec
    if (length(vec) > 2)
        ret <- c(vec[1], vec[length(vec)])
    return(ret)
}


str_right = function(string, n) {
    substr(string, nchar(string) - (n - 1), nchar(string))
}


str_left = function(string, n) {
    substr(string, 1, n)
}


add_file_prefix <- function(fpath, prefix){
    dir <- dirname(fpath)
    base <- basename(fpath)
    stopifnot(str_right(prefix, 1) != '_' && str_left(base, 1) != '_')
    return(file.path(dir, paste0(prefix, '_', base)))
}


nna_ratio <- function(x) {
    # 0 if all NA, 1 if all exist

    return(mean(!is.na(x)))
}


mean_nna <- function(x, nna_threshold = NULL){
    # mean skipping NA values,
    # if enough values exist above threshold ratio

    nna_mean <- mean(x, na.rm = TRUE)
    if (is.null(nna_threshold)) {
        return(nna_mean)
    } else {
        stopifnot(between(nna_threshold, 0, 1))
        if (nna_ratio(x) > nna_threshold)
            return(nna_mean)
        else
            return(NA)
    }
}


fmt_hm <- function(fp_hour){
    # formats time
    # 6.5 -> 06:30
    return(sprintf("%02i:%02i", trunc(fp_hour), trunc(fp_hour %% 1 * 60)))
}
