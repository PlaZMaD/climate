# formatR::tidy_rstudio()
library(REddyProc)
cat('REddyProc version: ', paste(packageVersion('REddyProc')), '\n')

source('src/reddyproc/web_tool_sources_adapted.r')
source('src/reddyproc/postprocess_calc_averages.r')
source('src/reddyproc/r_helpers.r')


EDDY_IMAGES_EXT <- '.png'
STATS_FNAME_EXT <- '.csv'
DATA_FNAME_END <- 'filled.txt'

# REddyProc library may rely on these global vars
INPUT_FILE <- NULL
OUTPUT_DIR <- NULL


# corresponds 06.2024 run
.eddyproc_all_required_options <- list(
    siteId = 'yourSiteID',

    isToApplyUStarFiltering = TRUE,
    # custom, not from default package; number or NULL
    ustar_fallback_value = 0.1,

    uStarSeasoning = factor("Continuous", levels = c("Continuous", "WithinYear", "User")),
    uStarMethod = factor("RTw", levels = "RTw"),

    isBootstrapUStar = FALSE,

    isToApplyGapFilling = TRUE,
    isToApplyPartitioning = TRUE,

    # "Reichstein05", "Lasslop10", ...
    partitioningMethods = c("Reichstein05", "Lasslop10"),
    latitude = 56.5,
    longitude = 32.6,
    timezone = +3,

    temperatureDataVariable = "Tair",
    daily_sums_units = list(NEE = 'TODO gC/m2/day', LE = 'Wm-2', H = 'Wm-2', Rg = 'Wm-2', Tair = 'degC',
                           Tsoil = 'degC', rH = '%', VPD = 'hPa', Ustar = 'ms-1', CH4flux = 'TODO mg_m-2_d-1'),

    isCatchingErrorsEnabled = TRUE,

    input_format = "onlinetool",
    output_format = "onlinetool",

    # figureFormat used from processEddyData
    useDevelopLibraryPath = FALSE,
    debugFlags = ""
)


.eddyproc_extra_options <- list(
    isCatchingErrorsEnabled = TRUE,

    input_format = "onlinetool",
    output_format = "onlinetool",

    # figureFormat used from processEddyData
    useDevelopLibraryPath = FALSE,
    debugFlags = ""
)


.merge_options <- function(user_opts, extra_opts){
    as_numeric_or_nan <- function (x) ifelse(is.null(x), NaN, as.numeric(x))

    merge <- list()

    merge$siteId <- user_opts$site_id

    merge$isToApplyUStarFiltering <- user_opts$is_to_apply_u_star_filtering
    merge$ustar_fallback_value <- as_numeric_or_nan(user_opts$ustar_fallback_value)
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
    merge$dailySumsUnits <- user_opts$daily_sums_units

    return(c(merge, extra_opts))
}


.finalise_config <- function(user_options){
    eddyproc_config <- .merge_options(user_options, .eddyproc_extra_options)

    got_types <- sapply(eddyproc_config, class)
    need_types <- sapply(.eddyproc_all_required_options, class)

    if (any(got_types != need_types)) {
        df_cmp = data.frame(got_types, need_types)
        cmp_str = paste(capture.output(df_cmp), collapse = '\n')
        stop("Incorrect options or options types: ", cmp_str)
    }
    return(eddyproc_config)
}


.reddyproc_io_wrapper <- function(eddyproc_config){
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


.reddyproc_ustar_fallback_wrapper <- function(eddyproc_config){
    res <- .reddyproc_io_wrapper(eddyproc_config)

    if (is.null(res$err$call))
        return(res)

    do_fallback <- FALSE

    # if REddypoc in ignore errors mode, stop will happend not on ustar failure, but later
    # res$err$message == 'must provide finite uStarThresholds', ..., ?
    if (grepl('sMDSGapFillAfterUstar', res$err$call, fixed = TRUE) %>% any)
        do_fallback <- TRUE

    # fallback if Rg (solar radiation) is missing, but required
    if (grepl('EProc$sEstUstarThold', res$err$call, fixed = TRUE) %>% any &&
        res$err$message == 'Missing columns in dataset: Rg')
        do_fallback <- TRUE

    if (do_fallback) {
        assert(eddyproc_config$isToApplyUStarFiltering, 'ustar failed while disabled.')
        warning('\n\nOPTION FAILURE: uStar filtering failed. \n',
                'Fallback attempt to eddyproc_config$isToApplyUStarFiltering = FALSE \n')

        eddyproc_config$isToApplyUStarFiltering <- FALSE
        res <- .reddyproc_io_wrapper(eddyproc_config)
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
    message("Output of R is truncated to improve rpy2 output.")

    INPUT_FILE <<- user_options$input_file
    OUTPUT_DIR <<- user_options$output_dir
    eddyproc_config <- .finalise_config(user_options)
    wr_res <- .reddyproc_ustar_fallback_wrapper(eddyproc_config)

    # processEddyData guaranteed to output equi-time-distant series
    dfs = calc_averages(wr_res$df_output)
    save_averages(dfs, OUTPUT_DIR, wr_res$out_prefix, STATS_FNAME_EXT)

    # wr_res$df_output better not be returned to python, since it's extra large df
    return(list(info = wr_res$EProc$sINFO, out_prefix = wr_res$out_prefix,
                changed_config = wr_res$changed_config))
}
