# this file allows running cell_reddyproc_process directly without rpy2
# which enables RStudio interactive debug

setwd(dirname(dirname(dirname(rstudioapi::getSourceEditorContext()$path))))
debugSource('test/reddyproc/helpers/init_test_env.r')

# uninstall REddyProc package and enable this for the full debug
# devtools::load_all(file.path(Sys.getenv('DEV'), '/R/REddyProc-1.3.3'), reset = TRUE)

debugSource('test/reddyproc/helpers/io.r')
debugSource('src/reddyproc/postprocess_calc_averages.r')
debugSource('src/reddyproc/web_tool_sources_adapted.r')
debugSource('src/reddyproc/reddyproc_wrapper.r')
debugSource('src/reddyproc/reddyproc_extensions.r')
debugSource('src/reddyproc/r_helpers.r')

# duplicates cell code to run from pure R
# avoiding R dupe here can be too complicated
rep_user_options <- list(
    site_id = 'tv_fy4',

    is_to_apply_u_star_filtering = TRUE,
    # NA to disable or double
    ustar_threshold_fallback = 0.1,
    # TODO remove leftovers after python Rg guess implemented
    # REP ustar requires Rg to detect nights; when real data is missing, 3 workarounds are possible
    # 'Rg_th_Py', 'Rg_th_REP' - estimate by theoretical algs,
    # 'Rg' - by real data, '' - ignore Rg and filter both days and nights
    ustar_rg_source = 'Rg',


    u_star_seasoning =  factor("Continuous", levels = c("Continuous", "WithinYear", "User")),
    u_star_method = factor("RTw", levels = "RTw"),

    is_bootstrap_u_star = FALSE,

    is_to_apply_gap_filling = TRUE,
    is_to_apply_partitioning = FALSE,

    partitioning_methods = c("Reichstein05", "Lasslop10"),
    latitude = 64.2,
    longitude = 100,
    timezone = +7,

    # TSoil
    temperature_data_variable = "Tair",

    input_file = "output/REddyProc.txt",
    output_dir = "output/reddyproc"
)


run_rep <- function(options, input_file = NULL) {
    # input_file = NULL to use path from options, usually project dir
    # input_file = *

    if (is.not.null(input_file)) {
        input_finfo <- find_rep_file(input_file)
        if (basename(input_finfo$fname) != basename(input_file))
            message('Using input file: ', input_finfo$fname)
        options$input_file <- input_finfo$fname
        options$site_id <- input_finfo$site_id
    }
    reddyproc_and_postprocess(options)

    # stopifnot(...)
    if (is.not.null(input_file)) {
        unexpected_out_dir = dirname(input_file) != dirname(options$output_dir)
        if (unexpected_out_dir)
            utils::browseURL(dirname(options$input_file))
    }
}


test_rep <- function(options, input_file) {
    # create a temp dir and run test in it

    # possibly copy all used files into temp dir and work only from it
    test_dir = tempdir()
    message('Test dir is: ', test_dir)

    options$input_file <- input_file
    options$output_dir <- test_dir
    run_rep(options, input_file)

    # stopifnot(...)


    utils::browseURL(test_dir)
}


# run_rep(rep_user_options)
run_rep(rep_user_options, 'output/*REddyProc*.txt')

# test_rep(rep_user_options, "test\\reddyproc\\test_process_fixtures\\test_3_years.txt")
# test_rep(rep_user_options, "test\\reddyproc\\test_process_fixtures\\test_3_months.txt")

