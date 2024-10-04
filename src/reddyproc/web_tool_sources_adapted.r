# This specific file was kindly provided by REddyProc authors
# Original file name is runEddyProcFunctions.R
# Contains minimal changes and is similar to online tool
# https://www.bgc-jena.mpg.de/REddyProc/ui/REddyProc.php


readInputData <- function(dataFileName, input_format) {
    if (input_format == "onlinetool") {
        fLoadTXTIntoDataframe(dataFileName, "") %>%
            fConvertTimeToPosix("YDH", Year = "Year", Day = "DoY", Hour = "Hour", TName = "DateTime")
    } else if (input_format == "fluxnet15") {
        fLoadFluxnet15(dataFileName)
    } else stop("unknown file format: ", input_format)
}


validateInputData <- function(inputData) {

    # delete empty columns in EddyData.F
    iEmptyCols <- which(colSums(is.na(inputData)) == nrow(inputData))
    if (length(iEmptyCols)) {
        warning("Columns ", paste(colnames(inputData)[iEmptyCols], collapse = ","), " have no data. They are not included in processing.")
        inputData <- inputData[, -iEmptyCols]
        # str(EddyData.F)
    }

    # test if VPD is there, if not calculate from Tair and rH
    if (!("VPD" %in% colnames(inputData))) {
        # calculate VPD
        print("Calculating VPD from rH and Tair.")
        c("rH", "Tair") %>%
            REddyProc:::fCheckColNum(inputData, ., "validateInputData")
        inputData$VPD <- fCalcVPDfromRHandTair(inputData$rH, inputData$Tair)
    }

    # filter long runs
    c("NEE") %>%
        REddyProc:::fCheckColNum(inputData, ., "validateInputData")
    inputData <- filterLongRuns(inputData, "NEE")
    inputData
}


getDataVariablesToFill <- function(allDataVariables, eddyProcConfiguration) {

    # user specified columns to be filled in addition to standard columns
    mdsVars <- allDataVariables[grep("_MDS$", allDataVariables)]

    dataVariablesToFill <- intersect(c("NEE", "LE", "H", "Rg", "VPD", "rH", "Tair", "Tsoil", mdsVars, eddyProcConfiguration$temperatureDataVariable),
        allDataVariables)

    # double check for us that temperature column really gets filled
    if (eddyProcConfiguration$isToApplyPartitioning) {
        if (!all(c(eddyProcConfiguration$temperatureDataVariable, "NEE", "Rg") %in% dataVariablesToFill))
            stop(paste0("Missing temperature variable (", eddyProcConfiguration$temperatureDataVariable, "), NEE or Rg.  Those are all required for flux partitioning!"))
    }
    cat("Data variables picked for gap filling (dataVariablesToFill): ", paste(dataVariablesToFill, collapse = ","), "\n")
    dataVariablesToFill
}


get_ustar_suffixes <- function(EProc) {
    if (nrow(EProc$sUSTAR_SCEN) == 0)
        return(character(0))
    names(EProc$sGetUstarScenarios())[-1L]
}


getAdditionalDataVariablesToKeep <- function(allDataVariables, keepDataVariables = character(0)) {
    addVariableNames <- intersect(keepDataVariables, allDataVariables)

    if (length(addVariableNames)) {
        cat("Additional columns picked to keep in processing: ", paste(addVariableNames, collapse = ","), "\n")
    } else cat("No additional columns picked to keep in processing\n")
    addVariableNames
}


.estUStarThreshold <- function(eddyProcConfiguration, EProc) {
    print("------------- u* Threshold estimation ---------------")

    nSample <- if (length(grep("fewNBootUStar", eddyProcConfiguration$debug)))
        3L else 200L

    seasonFactor <- if (eddyProcConfiguration$uStarSeasoning == "Continuous") {
        usCreateSeasonFactorMonth(EProc$sDATA$sDateTime, startMonth = c(3, 6, 9, 12))
    } else if (eddyProcConfiguration$uStarSeasoning == "WithinYear") {
        usCreateSeasonFactorMonthWithinYear(EProc$sDATA$sDateTime, startMonth = c(3, 6, 9, 12))
    } else if (eddyProcConfiguration$uStarSeasoning == "User") {
        if (is.null(EProc$sDATA$season))
            stop("Missing column season for user-specifid seasons for ", "u* Threshold estimation.")

        as.factor(EProc$sDATA$season)
    } else
        stop("unknown value of eddyProcConfiguration$uStarSeasoning")

    uStarRes <- if (isTRUE(eddyProcConfiguration$isBootstrapUStar)) {
        EProc$sEstUstarThresholdDistribution(seasonFactor = seasonFactor, nSample = nSample)
    } else {
        # EProc$trace(sEstUstarThold, browser);
        # EProc$untrace(sEstUstarThold) trace(usEstUstarThreshold, recover);
        # #untrace(usEstUstarThreshold) trace(REddyProc:::usGetValidUstarIndices, recover);
        # untrace(usGetValidUstarIndices)
        EProc$sEstUstarThold(seasonFactor = seasonFactor)
    }

    if (eddyProcConfiguration$uStarSeasoning == "User") {
        print(uStarRes[uStarRes$aggregationMode == "season", ])
        EProc$useSeaonsalUStarThresholds()
        # usGetSeasonalSeasonUStarMap(EProc$sGetEstimatedUstarThresholdDistribution()) Continuous, WithinYear
    } else {
        print(uStarRes[uStarRes$aggregationMode == "year", ])
        # usGetAnnualSeasonUStarMap(EProc$sGetEstimatedUstarThresholdDistribution())
        EProc$useAnnualUStarThresholds()
    }

    uStarTh <- EProc$sGetUstarScenarios()
    list(StarTh = EProc$sGetUstarScenarios(), seasonFactor = seasonFactor,
         suffixes = get_ustar_suffixes(EProc))
}


estUStarThresholdOrError <- function(eddyProcConfiguration, ...) {
    ans <- if (eddyProcConfiguration$isCatchingErrorsEnabled) {
        tryCatch({
            .estUStarThreshold(eddyProcConfiguration, ...)
        }, error = function(e) {
            print(paste("Error during GapFilling:", e$message))
            return(e)
        })
    } else {
        .estUStarThreshold(eddyProcConfiguration, ...)
    }
}


.getDataVariablesWithoutUncertainty <- function(eddyProcConfiguration, dataVariablesToFill) {
    # for some vars (meteo) calculating uncertainty makes no sense but takes long processing time
    dataVariablesWithoutUncertainty <- intersect(dataVariablesToFill, c("Rg", "VPD", "rH", "Tair", "Tsoil", eddyProcConfiguration$temperatureVarName))
}


# , uStarRes
.gapFillDataVariables <- function(EProc, eddyProcConfiguration, dataVariablesToFill) {
    dataVariablesWithoutUncertainty <- .getDataVariablesWithoutUncertainty(eddyProcConfiguration, dataVariablesToFill)
    for (dataVariable in dataVariablesToFill) {
        if (eddyProcConfiguration$isToApplyUStarFiltering && dataVariable == "NEE") {

            # only uStar bootstrap to NEE gapfilling, not to the other variables
            EProc$sMDSGapFillUStarScens(dataVariable, FillAll = !(dataVariable %in% dataVariablesWithoutUncertainty), isVerbose = TRUE)

            # EProc$sMDSGapFillAfterUStarDistr(dataVariable \t\t, uStarTh = uStarRes$uStarTh \t\t, uStarSuffixes =
            # uStarRes$suffixes \t\t, FillAll = !(dataVariable %in% dataVariablesWithoutUncertainty) \t\t, isVerbose = T)
        } else {
            EProc$sMDSGapFill(dataVariable, FillAll = !(dataVariable %in% dataVariablesWithoutUncertainty), isVerbose = T)
        }
    }
}


.computeSdNEE <- function(EProc) {
    # calculate the range over quantiles for each record suffixes <- EProc$sGetUstarSuffixes() # only in newer version
    suffixes <- names(EProc$sGetUstarScenarios())[-1L]
    if (length(suffixes) > 1L) {

        # if suffix is empty do not add underscore
        NEE_names <- paste0("NEE", ifelse(suffixes == "", "", "_"), suffixes, "_f")
        neeRange <- apply(EProc$sTEMP[, NEE_names], 1, function(x) {
            diff(range(x))
        })

        # assume gaussian distribution range = 2*1.96*sd
        EProc$sTEMP$NEE_fsdu <- neeRange/(2 * 1.96)

        # assume that errors are independent and variances up
        EProc$sTEMP$NEE_fsdug <- sqrt(EProc$sTEMP$NEE_uStar_fsd^2 + EProc$sTEMP$NEE_fsdu^2)
    }
}


.plotUnfilledDataVariables <- function(eddyProcConfiguration, EProc, dataVariablesToFill) {
    for (dataVariable in dataVariablesToFill) {
        EProc$sPlotFingerprint(dataVariable, Dir = OUTPUT_DIR, Format = eddyProcConfiguration$figureFormat)
        EProc$sPlotHHFluxes(dataVariable, Dir = OUTPUT_DIR, Format = eddyProcConfiguration$figureFormat)
    }

}


.plotFilledDataVariables <- function(eddyProcConfiguration, EProc, dataVariablesToFill) {
    processedEddyData <- EProc$sExportResults()
    vars_amend <- if ("NEE" %in% dataVariablesToFill)
        union("NEE_uStar", dataVariablesToFill) else dataVariablesToFill

    fillColnamesWithoutUncertainty <- .getDataVariablesWithoutUncertainty(eddyProcConfiguration, vars_amend)
    for (dataVariable in vars_amend) {
        baseNameVal <- paste(dataVariable, "f", sep = "_")
        baseNameSdVal <- ifelse(dataVariable %in% fillColnamesWithoutUncertainty, "none", paste(dataVariable, "fsd", sep = "_"))
        if (baseNameVal %in% colnames(processedEddyData)) {
            EProc$sPlotFingerprint(baseNameVal, Dir = OUTPUT_DIR, Format = eddyProcConfiguration$figureFormat)
            EProc$sPlotDiurnalCycle(baseNameVal, Dir = OUTPUT_DIR, Format = eddyProcConfiguration$figureFormat)
            EProc$sPlotDailySums(baseNameVal, VarUnc = baseNameSdVal, Dir = OUTPUT_DIR, Format = eddyProcConfiguration$figureFormat)
            EProc$sPlotHHFluxes(baseNameVal, Dir = OUTPUT_DIR, Format = eddyProcConfiguration$figureFormat)
        }
    }
}


.gapFillAndPlotDataVariables <- function(eddyProcConfiguration, EProc, dataVariablesToFill) {
    print("------------- Gapfilling ---------------")

    .gapFillDataVariables(EProc, eddyProcConfiguration, dataVariablesToFill)
    if (length(get_ustar_suffixes(EProc)))
        .computeSdNEE(EProc)

    .plotUnfilledDataVariables(eddyProcConfiguration, EProc, dataVariablesToFill)
    .plotFilledDataVariables(eddyProcConfiguration, EProc, dataVariablesToFill)
    # plotting results overview figures for gap filling
}


gapFillAndPlotDataVariablesOrError <- function(eddyProcConfiguration, ...) {
    if (eddyProcConfiguration$isCatchingErrorsEnabled) {
        tryCatch({
            .gapFillAndPlotDataVariables(eddyProcConfiguration, ...)
        }, error = function(e) {
            print(paste("Error during GapFilling:", e$message))
            return(e)
        })
    } else {
        .gapFillAndPlotDataVariables(eddyProcConfiguration, ...)
    }
}


.partitionFluxes <- function(EProc, eddyProcConfiguration) {
    EProc$sSetLocationInfo(LatDeg = eddyProcConfiguration$latitude, LongDeg = eddyProcConfiguration$longitude, TimeZoneHour = eddyProcConfiguration$timezone)
    TempVar = paste(eddyProcConfiguration$temperatureDataVariable, "_f", sep = "")
    QFTempVar = paste(eddyProcConfiguration$temperatureDataVariable, "_fqc", sep = "")
    uStarScenKeep = if ("U50" %in% get_ustar_suffixes(EProc))
        "U50" else "uStar"

    if (length(get_ustar_suffixes(EProc))) {
        # if (eddyProcConfiguration$isToApplyUStarFiltering){
        if ("Reichstein05" %in% eddyProcConfiguration$partitioningMethods) {
            resMR <- EProc$sMRFluxPartitionUStarScens(uStarScenKeep = uStarScenKeep, TempVar = TempVar, QFTempVar = QFTempVar,
                QFTempValue = 0)
        }
        if ("Lasslop10" %in% eddyProcConfiguration$partitioningMethods) {
            resGL <- EProc$sGLFluxPartitionUStarScens(uStarScenKeep = uStarScenKeep, TempVar = TempVar, QFTempVar = QFTempVar,
                QFTempValue = 0)
        }
    } else {
        if ("Reichstein05" %in% eddyProcConfiguration$partitioningMethods) {
            resMR <- EProc$sMRFluxPartition(TempVar = TempVar, QFTempVar = QFTempVar, QFTempValue = 0)
        }
        if ("Lasslop10" %in% eddyProcConfiguration$partitioningMethods) {
            resGL <- EProc$sGLFluxPartition(TempVar = TempVar, QFTempVar = QFTempVar, QFTempValue = 0)
        }
    }
}


.plotPartitionedFluxes <- function(eddyProcConfiguration, EProc) {
    suffix <- if (length(get_ustar_suffixes(EProc)))
        "_uStar" else ""

    plotFP <- function(varname) {
        if (varname %in% names(EProc$sTEMP)) {
            EProc$sPlotFingerprint(varname, Dir = OUTPUT_DIR, Format = eddyProcConfiguration$figureFormat, valueLimits = quantile(EProc$sTEMP[[varname]],
                prob = c(0, 0.99), na.rm = TRUE))
        } else {
            warning("\nColumn '", varname, "' not found. Aborting fingerprint plot.\n\n")
        }
    }

    if ("Reichstein05" %in% eddyProcConfiguration$partitioningMethods) {
        plotFP(paste0("Reco", suffix))
        plotFP(paste0("GPP", suffix, "_f"))
    }

    if ("Lasslop10" %in% eddyProcConfiguration$partitioningMethods) {
        plotFP(paste0("Reco_DT", suffix))
        plotFP(paste0("GPP_DT", suffix))
    }
}


.partitionAndPlotFluxes <- function(eddyProcConfiguration, EProc) {
    print("------------- Flux Partitioning ---------------")
    .partitionFluxes(EProc, eddyProcConfiguration)
    .plotPartitionedFluxes(eddyProcConfiguration, EProc)
}


partitionAndPlotFluxesOrError <- function(eddyProcConfiguration, ...) {
    if (eddyProcConfiguration$isCatchingErrorsEnabled) {
        tryCatch({
            .partitionAndPlotFluxes(eddyProcConfiguration, ...)
        }, error = function(e) {
            print(paste("Error during partitioning:", e$message))
            return(e)
        })
    } else {
        .partitionAndPlotFluxes(eddyProcConfiguration, ...)
    }
}


writeProcessingResultsToFile <- function(inputData, EProc, outputFileName,
                                         isIncludeOnlyFilledBootColumns = TRUE,
                                         output_format = "onlinetool") {
    ## output_format << if equals 'onlinetool' then for backward compatibility
    ##     the columns '*_ustar_*' are renamed to '*_*' in the generated output file

    processedEddyData <- EProc$sExportResults()
    if (isTRUE(isIncludeOnlyFilledBootColumns)) {

        # remove all columns generated during bootstrap, unless the filled,
        # which end with '_f' or start with Reco or start
        # with GPP
        suffixes <- get_ustar_suffixes(EProc)
        suffixes_boot <- suffixes[!(suffixes %in% c("", "uStar"))]
        iBootColsRemove <- unlist(sapply(suffixes_boot, function(suffix) {
            iBootCols <- grep(paste0("_", suffix), colnames(processedEddyData))

            # colnames(processedEddyData)[iBootCols]
            iKeepFilled <- grep("_f$", colnames(processedEddyData)[iBootCols])
            iKeepReco <- grep("^Reco_", colnames(processedEddyData)[iBootCols])
            iKeepGPP <- grep("^GPP_", colnames(processedEddyData)[iBootCols])
            iKeep <- sort(union(iKeepFilled, union(iKeepReco, iKeepGPP)))
            if (length(iKeep))
                iBootCols[-iKeep] else iBootCols
        }))

        # colnames(processedEddyData)[iBootColsRemove]
        if (length(iBootColsRemove))
            processedEddyData <- processedEddyData[, -iBootColsRemove]
    }
    if (output_format == "onlinetool") {
        names(processedEddyData) <- gsub("_uStar_", "_", names(processedEddyData))
        names(processedEddyData) <- gsub("_uStar$", "", names(processedEddyData))
    }

    # colnames(FilledEddyData.F) prepend user input file
    eddyProcOutputData <- cbind(inputData, processedEddyData)

    # fWriteDataframeToTextFile(outputFile = 'output.txt', Data.F = outDATA)
    if (output_format %in% c("onlinetool", "reddyproc12")) {
        fWriteDataframeToFile(eddyProcOutputData, FileName = outputFileName)
    } else if (output_format == "fluxnet15") {
        df_fn15 <- extract_FN15(EProc)

        # avoid readr dependency
        write.csv(df_fn15, outputFileName, row.names = FALSE, na = "-9999")
    } else stop("unknown output_format: ", output_format)

    return(eddyProcOutputData)
}


### string of 3 digits 0/1: u-starFiltering;gapFilling;Partitioning
encodeEddyProcTasks <- function(eddyProcConfiguration) {
    with(eddyProcConfiguration, {
        paste(if (isToApplyUStarFiltering)
            1 else 0, if (isToApplyGapFilling)
            1 else 0, if (isToApplyPartitioning)
            1 else 0, sep = "")
    })
}


.ustarThresholdFallback <- function(eddyProcConfiguration, EProc) {
    if (!anyNA(EProc$sUSTAR_SCEN$uStar))
        return()

    if (is.na(eddyProcConfiguration$ustar_fallback_value)) {
        warning('\n\nREddyProc uStar filter have not detected some thresholds.\n',
                'Fallback value is NaN. Gap fill failure is expected.\n')
        return()
    }

    before <- EProc$sUSTAR_SCEN
    EProc$sUSTAR_SCEN$uStar[is.na(EProc$sUSTAR_SCEN$uStar)] <-
        eddyProcConfiguration$ustar_fallback_value

    printed_df <- function(df)
        paste(capture.output(df), collapse = '\n')

    warning('\n\nREddyProc uStar filter have not automatically detected thresholds for some values.\n',
            'They were replaced with fixed fallback values. Before:\n',
            printed_df(before), '\nAfter: \n', printed_df(EProc$sUSTAR_SCEN), '\n')
}


processEddyData <- function(eddyProcConfiguration, dataFileName = INPUT_FILE,
                            outputFileName = file.path(OUTPUT_DIR, "output.txt"),
                            figureFormat = "pdf") {
    caught_error <- NULL


    eddyProcConfiguration$figureFormat <- figureFormat
    str(eddyProcConfiguration)

    inputData <- readInputData(dataFileName, eddyProcConfiguration$input_format)
    str(inputData)
    EddyDataWithPosix <- validateInputData(inputData)

    dataVariablesToFill <- getDataVariablesToFill(colnames(EddyDataWithPosix), eddyProcConfiguration)
    addVariableNames <- getAdditionalDataVariablesToKeep(colnames(EddyDataWithPosix), c("NEE_f", "NEE_fqc", paste(eddyProcConfiguration$temperatureDataVariable,
        c("_f", "_fqc"), sep = "")))

    # keep column season (if exists) for uStarFiltering
    if (eddyProcConfiguration$isToApplyUStarFiltering) {
        if ("Ustar" %in% colnames(EddyDataWithPosix))
            addVariableNames <- c(addVariableNames, "Ustar")
        if ("season" %in% colnames(EddyDataWithPosix))
            addVariableNames <- c(addVariableNames, "season")
    }

    EProc <- sEddyProc$new(eddyProcConfiguration$siteId, EddyDataWithPosix, union(dataVariablesToFill, addVariableNames), ColNamesNonNumeric = "season")

    if (eddyProcConfiguration$isToApplyUStarFiltering) {
        ans <- estUStarThresholdOrError(eddyProcConfiguration, EProc)
        if (!length(caught_error) && inherits(ans, "error"))
            caught_error <- ans
    }

    .ustarThresholdFallback(eddyProcConfiguration, EProc)

    if (eddyProcConfiguration$isToApplyGapFilling) {
        ans <- gapFillAndPlotDataVariablesOrError(eddyProcConfiguration, EProc, dataVariablesToFill)
        if (!length(caught_error) && inherits(ans, "error"))
            caught_error <- ans
    }

    if (eddyProcConfiguration$isToApplyPartitioning) {
        ans <- partitionAndPlotFluxesOrError(eddyProcConfiguration, EProc)
        if (!length(caught_error) && inherits(ans, "error"))
            caught_error <- ans
    }


    df_output <- writeProcessingResultsToFile(inputData, EProc, outputFileName = outputFileName,
                                              output_format = eddyProcConfiguration$output_format)
    ## value<< list of describe<< << string binary code 0/1 if UstarFiltering, GapFilling, FluxPartitioning was used <<
    ## string of size of the inputFile '<nrow>,<col>' << NULL or error object caught but not stopped << to end up in dump so
    ## that maybe debugged end<<

    return(list(mode = encodeEddyProcTasks(eddyProcConfiguration),
                inputSize = paste(dim(inputData), collapse = ","),
                err = caught_error, EProc = EProc, df_output = df_output))
}
