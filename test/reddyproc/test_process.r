# this file allows running cell_reddyproc_process directly without rpy2
# which enables RStudio interactive debug

setwd(dirname(dirname(dirname(rstudioapi::getSourceEditorContext()$path))))
debugSource('test/reddyproc/helpers/init_test_env.r')
# devtools::load_all(file.path(Sys.getenv('DEV'), '/R/REddyProc-1.3.3'), reset = TRUE)
debugSource('src/reddyproc/postprocess_calc_averages.r')
debugSource('src/reddyproc/web_tool_sources_adapted.r')
debugSource('src/reddyproc/reddyproc_wrapper.r')
debugSource('src/reddyproc/reddyproc_extensions.r')
debugSource('src/reddyproc/r_helpers.r')

# duplicates cell code to run from pure R
# avoiding R dupe here can be too complicated
eddyproc_user_options <- list(
    site_id = 'tv_fy4',

    is_to_apply_u_star_filtering = TRUE,
    # NA to disable or double
    ustar_threshold_fallback = 0.01,
    # TODO remove all after python Rg guess implemented
    # experimental option to apply uStar to all data (REP default is only nights), used only when Rg is missing
    ustar_allowed_on_days = TRUE,

    u_star_seasoning =  factor("Continuous", levels = c("Continuous", "WithinYear", "User")),
    u_star_method = factor("RTw", levels = "RTw"),

    is_bootstrap_u_star = FALSE,

    is_to_apply_gap_filling = TRUE,
    is_to_apply_partitioning = FALSE,

    partitioning_methods = c("Reichstein05", "Lasslop10"),
    latitude = 56.5,
    longitude = 32.6,
    timezone = +3,

    # TSoil
    temperature_data_variable = "Tair",

    input_file = "output/REddyProc_tv_fy4_2023.txt",
    output_dir = "output/reddyproc"
)


test_reddyproc <- function(options, input_file = NULL) {
    # input_file = NULL to use path from options, usually project dir

    # possibly copy all used files into temp dir and work only from it
    test_dir = tempdir()

    if (is.not.null(input_file)) {
        options$input_file <- input_file
        options$output_dir <- test_dir
    }
    reddyproc_and_postprocess(options)

    # stopifnot(...)
    if (is.not.null(input_file)) {
        message('Test dir is: ', test_dir)
        utils::browseURL(test_dir)
    }
}


test_reddyproc(eddyproc_user_options)
# test_reddyproc(eddyproc_user_options, "test\\reddyproc\\test_process_fixtures\\test_3_years.txt")
# test_reddyproc(eddyproc_user_options, "test\\reddyproc\\test_process_fixtures\\test_3_months.txt")
# test_reddyproc(eddyproc_user_options, "output/REddyProc.txt")
