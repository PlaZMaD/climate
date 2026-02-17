# this file is required because in Google Colab REddyProc is not default package and must be installed on every run

# 1.3.2 vs 1.3.3 have slightly different last columns
# alternative for windows
# install.packages('https://cran.r-project.org/bin/windows/contrib/4.1/REddyProc_1.3.2.zip', repos = NULL, type = "binary")


install_if_missing <- function(package, version, repos) {
    if (!require(package, character.only = TRUE)) {
        remotes::install_version(package, version = version, upgrade = "never", repos = repos)
        library(package, character.only = TRUE)
    }
}
# sink redirect is required to improve ipynb output
sink(stdout(), type = "message")
install_if_missing("REddyProc", "1.3.3", repos = 'https://cran.rstudio.com/')
sink()