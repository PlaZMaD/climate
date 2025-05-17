rm(list = ls())
rm(list = ls(environment(), all.names = TRUE))
gc()

# clear RStudio output
cat("\014")

# break into debug on error
# options(error = browser)

# no partial mathing
options("warnPartialMatchArgs" = TRUE)
options("warnPartialMatchAttr" = TRUE)
options("warnPartialMatchDollar" = TRUE)

# interactive() ?
# on_debug = function() {	cat("\014")	browser()}
# options(debugger = on_debug)

cat("Working dir is set to: ", getwd(), '\n')
