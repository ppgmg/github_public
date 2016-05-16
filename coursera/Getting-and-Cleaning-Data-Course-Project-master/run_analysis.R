## run_analysis.R
##
## This script performs the following functions:
##
## - merges the training and the test sets in the file given to 
##    create one data set;
## - extracts only the measurements on the mean and standard deviation 
##    for each measurement; 
## - uses descriptive activity names to name the activities 
##    in the data set;
## - appropriately labels the data set with descriptive 
##    variable names; and
## - from the data set created in the previous task, creates a second, 
##    independent tidy data set with the average of each variable 
##    for each activity and each subject.
##
## The tidy data set was written to a file **tidydata2.txt**, 
## which can be read in using a standard read.table() command 
## (for data with headers) when the file is in the current 
## working directory. For example:
##
## data <- read.table("tidydata2.txt",header=TRUE)
##
## Refer to the Codebook for descriptions of the variables in this dataset.
## Refer to the README file for further details on how this script works.

###########################################################################
##
## LOADING THE DATA
##

## Option 1:
## Here is the code for automatically retrieving data from the three 
## files constituting the test set, and the three files constituting
## the training set, within the ZIP file at the URL provided
##
## temp <- tempfile()
## download.file("https://d396qusza40orc.cloudfront.net/getdata%2Fprojectfiles%
##  2FUCI%20HAR%20Dataset.zip", temp, method="curl")
## testsubject <- read.table(unz(temp,"UCI HAR Dataset/test/subject_test.txt"))
## testx <- read.table(unz(temp,"UCI HAR Dataset/test/X_test.txt"))
## testy <- read.table(unz(temp,"UCI HAR Dataset/test/y_test.txt"))
## trainsubject<-read.table(unz(temp,"UCI HAR Dataset/train/subject_train.txt")
## trainx <- read.table(unz(temp,"UCI HAR Dataset/train/X_train.txt"))
## trainy <- read.table(unz(temp,"UCI HAR Dataset/train/y_train.txt"))
## unlink(temp)

## Option 2:
## Here is the code for loading data from the three files constituting
## the test set, and from the three files constituting the training set,
## assuming the "UCI HAR Dataset" folder (in unzipped form) is in the
## current working directory.

## load data from test set
testsubject <- read.table("UCI HAR Dataset/test/subject_test.txt")
testx <- read.table("UCI HAR Dataset/test/X_test.txt")
testy <- read.table("UCI HAR Dataset/test/y_test.txt")

## load data from training set
trainsubject <- read.table("UCI HAR Dataset/train/subject_train.txt")
trainx <- read.table("UCI HAR Dataset/train/X_train.txt")
trainy <- read.table("UCI HAR Dataset/train/y_train.txt")

## load dplyr package and re-store data in data frames
library(dplyr)
testsubDF <- tbl_df(testsubject)
rm(testsubject)
testDF <- tbl_df(testx)
rm(testx)
testactDF <- tbl_df(testy)
rm(testy)
trainsubDF <- tbl_df(trainsubject)
rm(trainsubject)
trainDF <- tbl_df(trainx)
rm(trainx)
trainactDF <- tbl_df(trainy)
rm(trainy)

#############################################################################
##
## MERGE THE TRAINING AND TEST DATA SETS
##

## bind columns in each of the test and training sets 
## then bind rows to combine both sets
mergeddataset <- rbind(cbind(testsubDF,testactDF,testDF),cbind(trainsubDF,
                        trainactDF,trainDF))

## preview details (commented in script)
## str(mergeddataset, list.len=10)

#############################################################################
##
## EXTRACT MEAN AND STANDARD DEVIATION MEASUREMENTS
##

## identify columns in original .x files to extract
itemstoextract <- list(1,2,3,4,5,6,41,42,43,44,45,46,81,82,83,84,85,86,121,122,
                       123,124,125,126,161,162,163,164,165,166,201,202,214,215,
                       227,228,240,241,253,254,266,267,268,269,270,271,294,295,
                       296,345,346,347,348,349,350,373,374,375,424,425,426,427,
                       428,429,452,453,454,503,504,513,516,517,526,529,530,539,
                       542,543,552)

## since our merged data set has two columns at the beginning
## we need to extract the columns of data using column indices 
## adjusted by 2, and then also extract the first two columns
## (subject & activity)
addtwo <- as.list(rep(2,length(itemstoextract)))
extractfromMerge <- mapply(function(x1,y1) x1[[1]]+y1[[1]], 
                           itemstoextract, addtwo)
extractfromMerge <- as.list(c(1,2,extractfromMerge))

## change variable names of first two columns (subject, activity)
## to avoid errors with duplicate column names
names(mergeddataset)[1] <- "subjectID"
names(mergeddataset)[2] <- "activityID"

## extract the columns and save in new data frame
extractedData <- select(mergeddataset,extractfromMerge)

## preview details (commented in actual code)
## str(extractedData, list.len=10)

############################################################################
##
## RENAME ACTIVITIES
##

## perform search and replace within activityID column
extractedData$activityID<-gsub(1,"walking",extractedData$activityID)
extractedData$activityID<-gsub(2,"walking upstairs",extractedData$activityID)
extractedData$activityID<-gsub(3,"walking downstairs",extractedData$activityID)
extractedData$activityID<-gsub(4,"sitting",extractedData$activityID)
extractedData$activityID<-gsub(5,"standing",extractedData$activityID)
extractedData$activityID<-gsub(6,"laying",extractedData$activityID)

## preview changes (commented in script)
## table(extractedData$activityID)

############################################################################
##
## RENAME COLUMN NAMES (VARIABLES)
##

## We define a namevariables function to handle the re-naming process
## Refer to the Codebook for descriptions of the variables in this dataset
namevariables <- function(df) {
    names(df)[names(df)=="V1"] <- "mean body acceleration X axis"
    names(df)[names(df)=="V2"] <- "mean body acceleration Y axis"
    names(df)[names(df)=="V3"] <- "mean body acceleration Z axis"
    names(df)[names(df)=="V4"] <- "std. dev. body acceleration X axis"
    names(df)[names(df)=="V5"] <- "std. dev. body acceleration Y axis"
    names(df)[names(df)=="V6"] <- "std. dev. body acceleration Z axis"
    names(df)[names(df)=="V41"] <- "mean gravity acceleration X axis"
    names(df)[names(df)=="V42"] <- "mean gravity acceleration Y axis"    
    names(df)[names(df)=="V43"] <- "mean gravity acceleration Z axis"
    names(df)[names(df)=="V44"] <- "std. dev. gravity acceleration X axis"
    names(df)[names(df)=="V45"] <- "std. dev. gravity acceleration Y axis"
    names(df)[names(df)=="V46"] <- "std. dev. gravity acceleration Z axis"
    names(df)[names(df)=="V81"] <- "mean jerk X axis"
    names(df)[names(df)=="V82"] <- "mean jerk Y axis"
    names(df)[names(df)=="V83"] <- "mean jerk Z axis"
    names(df)[names(df)=="V84"] <- "std. dev. jerk X axis"
    names(df)[names(df)=="V85"] <- "std. dev. jerk Y axis"
    names(df)[names(df)=="V86"] <- "std. dev. jerk Z axis"
    names(df)[names(df)=="V121"] <- "mean angular velocity X axis"
    names(df)[names(df)=="V122"] <- "mean angular velocity Y axis"
    names(df)[names(df)=="V123"] <- "mean angular velocity Z axis"
    names(df)[names(df)=="V124"] <- "std. dev. angular velocity X axis"
    names(df)[names(df)=="V125"] <- "std. dev. angular velocity Y axis"
    names(df)[names(df)=="V126"] <- "std. dev. angular velocity Z axis"
    names(df)[names(df)=="V161"] <- "mean angular jerk X axis"
    names(df)[names(df)=="V162"] <- "mean angular jerk Y axis"
    names(df)[names(df)=="V163"] <- "mean angular jerk Z axis"
    names(df)[names(df)=="V164"] <- "std. dev. angular jerk X axis"
    names(df)[names(df)=="V165"] <- "std. dev. angular jerk Y axis"
    names(df)[names(df)=="V166"] <- "std. dev. angular jerk Z axis"
    names(df)[names(df)=="V201"] <- "mean body acceleration"
    names(df)[names(df)=="V202"] <- "std. dev. body acceleration"
    names(df)[names(df)=="V214"] <- "mean gravity acceleration"
    names(df)[names(df)=="V215"] <- "std. dev. gravity acceleration"
    names(df)[names(df)=="V227"] <- "mean jerk"
    names(df)[names(df)=="V228"] <- "std. dev. jerk"
    names(df)[names(df)=="V240"] <- "mean angular velocity"
    names(df)[names(df)=="V241"] <- "std. dev. angular velocity"
    names(df)[names(df)=="V253"] <- "mean angular jerk"
    names(df)[names(df)=="V254"] <- "std. dev. angular jerk"
    names(df)[names(df)=="V266"] <- "mean body acceleration X axis freq. domain"
    names(df)[names(df)=="V267"] <- "mean body acceleration Y axis freq. domain"
    names(df)[names(df)=="V268"] <- "mean body acceleration Z axis freq. domain"
    names(df)[names(df)=="V269"] <- "std. dev. body acceleration X axis 
                                        freq. domain"
    names(df)[names(df)=="V270"] <- "std. dev. body acceleration Y axis 
                                        freq. domain"
    names(df)[names(df)=="V271"] <- "std. dev. body acceleration Z axis 
                                        freq. domain"
    names(df)[names(df)=="V294"] <- "wtd. avg. of freq. components body acc. 
                                        X axis"
    names(df)[names(df)=="V295"] <- "wtd. avg. of freq. components body acc. 
                                        Y axis"
    names(df)[names(df)=="V296"] <- "wtd. avg. of freq. components body acc. 
                                        Z axis"
    names(df)[names(df)=="V345"] <- "mean jerk X axis freq. domain"
    names(df)[names(df)=="V346"] <- "mean jerk Y axis freq. domain"
    names(df)[names(df)=="V347"] <- "mean jerk Z axis freq. domain"
    names(df)[names(df)=="V348"] <- "std. dev. jerk X axis freq. domain"
    names(df)[names(df)=="V349"] <- "std. dev. jerk Y axis freq. domain"
    names(df)[names(df)=="V350"] <- "std. dev. jerk Z axis freq. domain"
    names(df)[names(df)=="V373"] <- "wtd. avg. of freq. components jerk X axis"
    names(df)[names(df)=="V374"] <- "wtd. avg. of freq. components jerk Y axis"
    names(df)[names(df)=="V375"] <- "wtd. avg. of freq. components jerk Z axis"
    names(df)[names(df)=="V424"] <- "mean angular velocity X axis freq. domain"
    names(df)[names(df)=="V425"] <- "mean angular velocity Y axis freq. domain"
    names(df)[names(df)=="V426"] <- "mean angular velocity Z axis freq. domain"
    names(df)[names(df)=="V427"] <- "std. dev. angular velocity X axis 
                                        freq. domain"
    names(df)[names(df)=="V428"] <- "std. dev. angular velocity Y axis 
                                        freq. domain"
    names(df)[names(df)=="V429"] <- "std. dev. angular velocity Z axis 
                                        freq. domain"
    names(df)[names(df)=="V452"] <- "wtd. avg. freq. components ang. velocity 
                                        X axis"
    names(df)[names(df)=="V453"] <- "wtd. avg. freq. components ang. velocity 
                                        Y axis"
    names(df)[names(df)=="V454"] <- "wtd. avg. freq. components ang. velocity 
                                        Z axis"
    names(df)[names(df)=="V503"] <- "mean body acceleration freq. domain"
    names(df)[names(df)=="V504"] <- "std. dev. body acceleration freq. domain"
    names(df)[names(df)=="V513"] <- "wtd. avg. freq. components body acc."
    names(df)[names(df)=="V516"] <- "mean jerk freq. domain"
    names(df)[names(df)=="V517"] <- "std. dev. jerk freq. domain"
    names(df)[names(df)=="V526"] <- "wtd. avg. freq. components jerk"
    names(df)[names(df)=="V529"] <- "mean angular velocity freq. domain"
    names(df)[names(df)=="V530"] <- "std. dev. angular velocity freq. domain"
    names(df)[names(df)=="V539"] <- "wtd. avg. freq. components 
                                        angular velocity"
    names(df)[names(df)=="V542"] <- "mean angular jerk freq. domain"
    names(df)[names(df)=="V543"] <- "std. dev. angular jerk freq. domain"
    names(df)[names(df)=="V552"] <- "wtd. avg. freq. components angular jerk"
    
    df
}

cleandata <- namevariables(extractedData)
## cleandata <- extractedData

## preview details (commented in script)
## str(cleandata, list.len=10)

#############################################################################
##
## CREATE A NEW DATA SET WITH AVERAGE OF EACH VARIABLE  
## FOR EACH ACTIVITY AND EACH SUBJECT
##

## group by both subjectID and activityID
## then calculate mean, for each variable by group
tidydata2 <- group_by(cleandata, subjectID, activityID)
tidydata2 <- summarise_each(tidydata2, funs(mean), -subjectID, -activityID)

## add prefix "GroupAvg" to variable names to identify values as group averages
colnames(tidydata2) <- paste("GroupAvg", colnames(tidydata2), sep=":")
names(tidydata2)[1] <- "subjectID"   ## reset first column header
names(tidydata2)[2] <- "activityID"  ## reset second column header

## preview details (commented in script)
## str(tidydata2, list.len=10)

#############################################################################
##
## WRITE DATA TO A FILE
## 

## Refer to the Codebook for descriptions of the variables in this dataset
write.table(tidydata2, file="tidydata2.txt", row.names=FALSE)

## To read this file, when in the current working directory:
## data <- read.table("tidydata2.txt",header=TRUE)
