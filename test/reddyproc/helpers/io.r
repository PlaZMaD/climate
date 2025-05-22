find_rep_file <- function(path_mask) {
	matches <- Sys.glob(path_mask)
	stopifnot(length(matches) == 1)

	fname <- matches[1]

	stem <- tools::file_path_sans_ext(basename(fname))
	site_id <- sub("^REddyProc_(.*?)(?:_\\d).*", "\\1", stem)

	list(fname = fname, site_id = site_id)
}
