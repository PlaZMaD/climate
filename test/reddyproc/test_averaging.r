# tests specifically for calc_averages

setwd(dirname(dirname(dirname(rstudioapi::getSourceEditorContext()$path))))
debugSource('test/reddyproc/helpers/init_test_env.r')
debugSource('src/reddyproc/postprocess_calc_averages.r')
debugSource('src/reddyproc/r_helpers.r')


test_dir = tempdir()


ensure_correct_names <- function(nd, nm, ny){
	stopifnot(!duplicated(nd), !duplicated(nm), !duplicated(ny))
	stopifnot(setdiff(nd, c('DoY', 'DoM')) == nm, setdiff(nm, 'Month') == ny)

	# no with .1 in name
	stopifnot(!any(contains(match = '.1', vars = c(nd, nm, ny))))
}


save_reddyproc_df <- function(df, fname) {
	df_save <- df
	df_save$DateTime <- as.character(format(df$DateTime, "%Y-%m-%d %H:%M:%S"))
	write.csv(df_save, file = fname, row.names = FALSE, quote = FALSE)
}


load_csv_as_reddyproc_df <- function(fname, tz = 'UTC') {
	df <- read.csv(fname, quote = NULL,  row.names = NULL)
	if (!is.null(df$season))
		df$season <- factor(df$season)
	df$DateTime <- as.POSIXct(df$DateTime, tz = tz, format = "%Y-%m-%d %H:%M:%S")

	# all.equal(test, df_full, tolerance = 1e-8)
	# all.equal(test, df_full, tolerance = 1e-8, check.attributes = FALSE)
	return(df)
}


test_model_3_month <- function(){
	df = load_csv_as_reddyproc_df('test/reddyproc/test_averaging_fixtures/tm1_3m_2y.csv', tz = 'GMT')

	YM <- df$Year[10]
	YB <- YM - 1
	YA <- YM + 1

	# ensure order and years are processed separately
	df[df$Year == YM & df$DoY == 354 & df$Hour > 10,]$Year = YB
	df[df$Year == YB & df$DoY == 354,]$LE_f = 17
	df[df$Year == YM & df$DoY == 354,]$LE_f = 11

	# ensure missing columns won't break
	df$NEE_f = NULL

	# ensure average
	stopifnot(df[df$Year == YA & between(df$DoY, 32, 59),]$Rg_f %>%
			  	mean %>% between(46.6980, 46.6981))

	# ensure NA calculated correctly
	df[df$Year == YA & between(df$DoY, 1, 31),]$H = NA

	dfs <- calc_averages(df)

	# save_reddyproc_df(df, fname = fs::path(tempdir(), 'test_mon_input_df.csv'))
	df <- NULL

	dd <- dfs$daily
	dm <- dfs$monthly
	dy <- dfs$yearly
	dh <- dfs$hourly

	# ensure years are processed separately
	stopifnot(dd[dd$Year == YB & dd$DoY == 354,]$LE_f == 17)
	stopifnot(dd[dd$Year == YM & dd$DoY == 354,]$LE_f == 11)

	# ensure order
	stopifnot(dm$Year[1] == YB & dm$Year[nrow(dm)] == YA)

	# ensure missing columns won't break
	stopifnot(!'NEE_f' %in% colnames(dm), !'NEE' %in% colnames(dd))

	#  ensure average
	stopifnot(dm[dm$Year == YA & dm$Month == 2,]$Rg_f %>%
			  	between(46.6980, 46.6981))

	# ensure NA calculated correctly
	stopifnot(dm[dm$Year == YA & dm$Month == 1,]$H_sqc == 0.0)

	# some math can lead to undesired NaN

	stopifnot(!anyNAN(dy), !anyNAN(dm), !anyNAN(dd), !anyNAN(dh))

	ensure_correct_names(names(dd), names(dm), names(dy))
	cat('Test test_model_3_month ok \n\n')
}


test_real_year <- function(){
	df = load_csv_as_reddyproc_df('test/reddyproc/test_averaging_fixtures/tm2_2y.csv')

	YM <- df$Year[10]
	YB <- YM - 1
	YA <- YM + 1

	# ensure order and years are processed separately
	df[df$Year == YM & df$DoY == 354 & df$Hour > 10,]$Year = YB
	df[df$Year == YM & df$DoY == 354,]$LE_f = 17
	df[df$Year == YB & df$DoY == 354,]$LE_f = 11

	# ensure average
	row_mask = df$Year == YM & between(df$DoY, 325, 365)
	df[row_mask,]$VPD_f = df[row_mask,]$DoY

	# ensure hourly
	mask = df$Year == YM & month(df$DateTime) == 4 & between(df$Hour, 8, 10)
	df[mask,]$H_f <- df[mask,]$Hour
	mask = df$Year == YM & month(df$DateTime) == 5
	df[mask,]$H_f <- 24 - df[mask,]$Hour
	df[mask & df$DoY == 130,]$H_f <- -100

	# ensure hourly sqc
	df[mask,]$H <- df[mask,]$Hour * -2.5
	df[mask & day(df$DateTime) == 2,]$H <- NA

	# ensure single row val and
	one_year_tail <- tail(df, 1)
	one_year_tail$Year <- one_year_tail$Year + 1
	one_year_tail$VPD <- NA
	one_year_tail$VPD_f <- NA
	df <- rbind(df, one_year_tail)
	YL <-  df[nrow(df),]$Year

	# ensure single row last year excluded
	one_year_tail$Year <- one_year_tail$Year + 1
	df <- rbind(df, one_year_tail)

	# ensure NA calculated correctly
	nna_prc <- df[df$Year == YB & df$DoY == 354,]$LE %>% {mean(!is.na(.))}
	df[df$Year == YM & between(df$DoY, 1, 31),]$H_f <- NA
	stopifnot(df[df$Year == YB & between(df$DoY, 1, 31),]$H %>% is.na)
	df[df$Year == YM & between(df$DoY, 335, 365),]$H <- -5

	# ensure no interference from similar columns
	df$VPD_ff = df$DoY
	df$VVPD_ff = df$DoY

	# ensure length
	iso_mon <- month(ISOdate(year = df$Year, month = 1, day = 1) + days(df$DoY - 1))
	stopifnot(month(df$DateTime) == iso_mon)

	expected_years = n_distinct(df$Year)
	expected_months = n_distinct(cbind(df$Year, iso_mon))
	expected_days = n_distinct(cbind(df$Year, df$DoY))
	expected_hours = n_distinct(cbind(df$Year, iso_mon, df$Hour))

	dfs <- calc_averages(df)

	# save_reddyproc_df(df, fname = fs::path(tempdir(), 'test_year_input_df.csv'))
	df <- NULL

	dt <- dfs$hourly
	dd <- dfs$daily
	dm <- dfs$monthly
	dy <- dfs$yearly

	# ensure years are processed separately
	stopifnot(dd[dd$Year == YM & dd$DoY == 354,]$LE_f == 17)
	stopifnot(dd[dd$Year == YB & dd$DoY == 354,]$LE_f == 11)

	# ensure order
	stopifnot(dm$Year[1] == YB & dm$Year[nrow(dm)] == YL)

	#  ensure average
	stopifnot(dm[dm$Year == YM & dm$Month == 12,]$VPD_f %>% between(31*11, 31*12))

	# ensure hourly
	mask_1 <- dt$Year == YM & dt$Month == 4 & dt$Hour == 9
	not_mask_1 <- dt$Year == YM & dt$Month == 5 & dt$Hour == 9
	not_mask_2 <- dt$Year == YM & dt$Month == 6 & dt$Hour == 11
	stopifnot(dt[mask_1,]$H_f == 9, dt[not_mask_1,]$H_f != 9, dt[not_mask_2,]$H_f != 9)

	# ensure hourly sqc
	mask_2 <- dt$Year == YM & dt$Month == 5 & dt$Hour == 20
	stopifnot(dt[mask_2,]$H_f == ((24 - 20) * 30 - 100) / 31)
	stopifnot(dt[mask_2,]$H_sqc == 30 / 31)

	# ensure single row val
	stopifnot(any(dd[dd$Year == YM,]$VPD_sqc != 0), dd[dd$Year == YL,]$VPD_sqc == 0)
	stopifnot(!anyNA(dy[dy$Year == YM,]$VPD_f), dy[dy$Year == YL,]$VPD_f %>% is.na)

	# ensure length
	stopifnot(nrow(dy) == expected_years - 1)
	stopifnot(nrow(dm) == expected_months - 1)
	stopifnot(nrow(dd) == expected_days - 1)
	stopifnot(nrow(dt) == expected_hours - 1)

	# some math can lead to undesired NaN
	stopifnot(!anyNAN(dy), !anyNAN(dm), !anyNAN(dd), !anyNAN(dt))

	ensure_correct_names(names(dd), names(dm), names(dy))
	save_averages(dfs, tempdir(), 'tmp', '.csv')
	cat('Test test_real_year ok \n\n')
}

# TODO not coverred by any tests: output csv will contain not numbers, but strings in some cases
test_real_year()
test_model_3_month()
