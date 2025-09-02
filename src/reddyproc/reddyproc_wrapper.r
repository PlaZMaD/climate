# formatR::tidy_rstudio()
library(REddyProc)
cat('REddyProc version: ', paste(packageVersion('REddyProc')), '\n')

# must be preset be caller env, script-wide routine
stopifnot(file.exists(repo_dir))
repo_path <- function(src_path) {file.path(repo_dir, src_path)}

source('src/reddyproc/web_tool_sources_adapted.r' %>% repo_path)
source('src/reddyproc/postprocess_calc_means.r' %>% repo_path)
source('src/reddyproc/r_helpers.r' %>% repo_path)


EDDY_IMAGES_EXT <- '.png'
STATS_FNAME_EXT <- '.csv'
DATA_FNAME_END <- 'filled.txt'

# REddyProc library may rely on these global vars
INPUT_FILE <- NULL
OUTPUT_DIR <- NULL


.reddyproc_user_config_types <- sapply(list(
    siteId = 'DefaultID',

    isToApplyUStarFiltering = FALSE,
    ustar_threshold_fallback = 0.123456,
    ustar_rg_source = 'Column name',

    uStarSeasoning = factor("Continuous", levels = c("Continuous", "WithinYear", "User")),
    uStarMethod = factor("RTw", levels = "RTw"),

    isBootstrapUStar = FALSE,

    isToApplyGapFilling = TRUE,
    isToApplyPartitioning = TRUE,

    partitioningMethods = c("Reichstein05", "Lasslop10"),
    latitude = 56.5,
    longitude = 32.6,
    timezone = +3,

    t_temperatureDataVariable = "Tair"
), class)


# unlike template, is actually applied
.reddyproc_extra_config <- list(
    isCatchingErrorsEnabled = TRUE,

    input_format = "onlinetool",
    output_format = "onlinetool",

    # figureFormat used from processEddyData
    useDevelopLibraryPath = FALSE,
    debugFlags = ""
)


.convert_options_types <- function(user_opts){
    as_numeric_or_nan <- function(x) ifelse(is.null(x), NaN, as.numeric(x))

    merge <- list()

    merge$siteId <- user_opts$site_id

    merge$isToApplyUStarFiltering <- user_opts$is_to_apply_u_star_filtering
    merge$ustar_threshold_fallback <- as_numeric_or_nan(user_opts$ustar_threshold_fallback)
    merge$ustar_rg_source  <- user_opts$ustar_rg_source

    merge$uStarSeasoning <- factor(user_opts$u_star_seasoning)
    merge$uStarMethod <- factor(user_opts$u_star_method)

    merge$isBootstrapUStar <- user_opts$is_bootstrap_u_star

    merge$isToApplyGapFilling <- user_opts$is_to_apply_gap_filling
    merge$isToApplyPartitioning <- user_opts$is_to_apply_partitioning

    merge$partitioningMethods <- user_opts$partitioning_methods
    merge$latitude <- as.numeric(user_opts$latitude)
    merge$longitude <- as.numeric(user_opts$longitude)
    merge$timezone <- as.numeric(user_opts$timezone)

    merge$temperatureDataVariable <- user_opts$temperature_data_variable

    return(merge)
}


.finalise_config <- function(user_options){
    user_config <- .convert_options_types(user_options)

    got_types <- sapply(user_config, class)
    need_types <- .reddyproc_user_config_types

    if (any(got_types != need_types)) {
        df_cmp = data.frame(got_types, need_types)
        cmp_str = paste(capture.output(df_cmp), collapse = '\n')
        stop("Incorrect options or options types: ", cmp_str)
    }

    return(c(user_config, .reddyproc_extra_config))
}


.run_reddyproc_via_io_wrapper <- function(eddyproc_config){
    # more specifically, still calls processEddyData wrapper from web tool,
    # which finally calls REddyProc library

    dir.create(OUTPUT_DIR, showWarnings = FALSE, recursive = TRUE)

    clean_out_files <- function(fname_end)
        unlink(file.path(OUTPUT_DIR, paste0('*', fname_end)))
    clean_out_files(EDDY_IMAGES_EXT)
    clean_out_files(STATS_FNAME_EXT)
    clean_out_files(DATA_FNAME_END)

    output_file <- file.path(OUTPUT_DIR, DATA_FNAME_END)
    res <- processEddyData(eddyproc_config, dataFileName = INPUT_FILE,
                           outputFileName = output_file,
                           figureFormat = tools::file_ext(EDDY_IMAGES_EXT))

    res$out_prefix <- paste0(eddyproc_config$siteId, '_' , res$EProc$sINFO$Y.NAME)
    file.rename(output_file, add_file_prefix(output_file, res$out_prefix))

	return(res)
}


.run_reddyproc_via_ustar_fallback_wrapper <- function(eddyproc_config){
    res <- .run_reddyproc_via_io_wrapper(eddyproc_config)

    if (is.null(res$err$call))
        return(res)

    do_fallback <- FALSE

    # if REddypoc in ignore errors mode, error stop will happend not on ustar failure, but later
    # TODO 3 try to find to more specified check not before the next release
    # res$err$message == 'must provide finite uStarThresholds', ..., ?
    if (grepl('sMDSGapFillAfterUstar', res$err$call, fixed = TRUE) %>% any)
        do_fallback <- TRUE

    # fallback if Rg (solar radiation) is missing, but required
    if (is_error_ustar_need_rg(res$err))
        do_fallback <- TRUE

    if (do_fallback) {
        assert(eddyproc_config$isToApplyUStarFiltering, 'ustar failed while disabled.')
        warning('\n', RE, RU, 'Ustar filtering failed. \n',
                'Fallback attempt to isToApplyUStarFiltering = FALSE \n')

        eddyproc_config$isToApplyUStarFiltering <- FALSE
        res <- .run_reddyproc_via_io_wrapper(eddyproc_config)
        res$changed_config <- eddyproc_config
    }


    return(res)
}


reddyproc_and_postprocess <- function(user_options){
    # combined function to avoid converting output or using global env

    # stderr was missing in rpy2 and this was a fix,
    # but now stderr and stdout are merged in wrapper
    # sink(stdout(), type = "message", split = TRUE)

    # display warnings immidiately; REddyProc web tool uses this
    options(warn = 1)

    options(max.print = 50)
    message(RE, 'Max length of R output is reduced to improve rpy2 output.')

    INPUT_FILE <<- user_options$input_file
    OUTPUT_DIR <<- user_options$output_dir
    eddyproc_config <- .finalise_config(user_options)
    wr_res <- .run_reddyproc_via_ustar_fallback_wrapper(eddyproc_config)

    # processEddyData guaranteed to output equi-time-distant series
    dfs = calc_averages(wr_res$df_output)
    save_averages(dfs, OUTPUT_DIR, wr_res$out_prefix, STATS_FNAME_EXT)

    # wr_res$df_output better not be returned to python, since it's extra large df
    return(list(info = wr_res$EProc$sINFO, out_prefix = wr_res$out_prefix,
                changed_config = wr_res$changed_config))
}
