Getting and Cleaning Data Course Project
========================================
submitted by: ppgmg

## README.md

For this project, I created an R script called *run_analysis.R* that does the following:

- merges the training and the test sets in the file given to create one data set;
- extracts only the measurements on the mean and standard deviation for each measurement; 
- uses descriptive activity names to name the activities in the data set;
- appropriately labels the data set with descriptive variable names; and
- from the data set created in the previous task, creates a second, independent tidy data set with the average of each variable for each activity and each subject.

The tidy data set was written to a file **tidydata2.txt**, which can be read in using a standard read.table() command (for data with headers) when the file is in the current working directory: 


```r
data <- read.table("tidydata2.txt",header=TRUE)
```

This README file describes how the script works, and accompanies a code book *CodeBook.md* that describes the variables of the intermediate data set with the extracted data, and the variables in the newly created tidy data set.  

*Note: I have gone into a little more depth here than is typically necessary for a README file, to preserve an account of my thought process for this project that may assist me in future assignments.*

### Notes on running the script

The file *run_analysis.R* should be saved in a directory where the folder containing the downloaded data is also stored (after being unzipped), if the script is to be executed. That is, the working directory should contain the folder "UCI HAR Dataset". However, I have also included code (in comments) below that will automatically download the provided ZIP file from the URL provided, and extract the needed files stored in that ZIP file into the current working directory.

Required packages to run scripts: **dplyr**

### Files in this submission

The files constituting this assignment submission include:

- **run_analysis.R**: the script used to generate a new tidy data set with the average of each variable for each activity and each subject
- **tidydata2.txt**: the new tidy data set created with the script
- **README.md**: the current document
- **CodeBook.md**: a document describing the variables in the new data set

## Description of work performed by the script

### Introduction

This assignment makes use of data from a personal activity monitoring device. The experiments have been carried out with a group of 30 volunteers within an age bracket of 19-48 years. Each person performed six activities (WALKING, WALKING_UPSTAIRS, WALKING_DOWNSTAIRS, SITTING, STANDING, LAYING) wearing a smartphone (Samsung Galaxy S II) on the waist. Using its embedded accelerometer and gyroscope, 3-axial linear acceleration and 3-axial angular velocity at a constant rate of 50Hz were captured. 

The obtained dataset was randomly partitioned into two sets, where 70% of the volunteers was selected for generating the training data and 30% the test data. Further details on the data used for this assignment can be found at: http://archive.ics.uci.edu/ml/datasets/Human+Activity+Recognition+Using+Smartphones.

The data used to generate this report was downloaded from the course web site, at the URL provided, on Sat Dec 13 17:50:11 2014.

First, I included within the comments of my script, several commands to automatically download the dataset into memory, and extract the files *subject_test.txt*, *X_test.txt*, and *y_test.txt* from the *UCI HAR Dataset/test* directory, and the files *subject_train.txt*, *X_train.txt*, and *y_train.txt* from the *UCI HAR Dataset/train* directory. (Note: I did not download inertial signal data given the emphasis on mean and standard deviation measures in this assignment.)

However, to satisfy the requirements of this assignment, I have also included executable code that will allow the data to be loaded with the data file already downloaded and unzipped in the current working directory.

The data was then loaded into six corresponding objects, for further processing.


```r
## Option 1:
## Here is the code for automatically retrieving data from the three 
## files constituting the test set, and the three files constituting
## the training set, within the ZIP file at the URL provided
##
## temp <- tempfile()
## download.file("https://d396qusza40orc.cloudfront.net/getdata%2Fprojectfiles%2FUCI%20HAR%20Dataset.zip", temp, method="curl")
## testsubject <- read.table(unz(temp,"UCI HAR Dataset/test/subject_test.txt"))
## testx <- read.table(unz(temp,"UCI HAR Dataset/test/X_test.txt"))
## testy <- read.table(unz(temp,"UCI HAR Dataset/test/y_test.txt"))
## trainsubject <- read.table(unz(temp,"UCI HAR Dataset/train/subject_train.txt")
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
```

The *dplyr* package was used. After loading this package, the data in the six data objects were stored in corresponding data frame objects.


```r
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
```

### Part 1: Merge the training and the test sets to create one data set

I then merged the two sets together to create a single data set. This involved binding together the subject and activity data with the measurement data for each of the training and test sets separately, and then subsequently combining the records of the training set with the records of the test set.


```r
## bind columns in each of the test and training sets 
## then bind rows to combine both sets
mergeddataset <- rbind(cbind(testsubDF,testactDF,testDF),cbind(trainsubDF,trainactDF,trainDF))

## preview details (commented in script)
str(mergeddataset, list.len=10)
```

```
## 'data.frame':	10299 obs. of  563 variables:
##  $ V1  : int  2 2 2 2 2 2 2 2 2 2 ...
##  $ V1  : int  5 5 5 5 5 5 5 5 5 5 ...
##  $ V1  : num  0.257 0.286 0.275 0.27 0.275 ...
##  $ V2  : num  -0.0233 -0.0132 -0.0261 -0.0326 -0.0278 ...
##  $ V3  : num  -0.0147 -0.1191 -0.1182 -0.1175 -0.1295 ...
##  $ V4  : num  -0.938 -0.975 -0.994 -0.995 -0.994 ...
##  $ V5  : num  -0.92 -0.967 -0.97 -0.973 -0.967 ...
##  $ V6  : num  -0.668 -0.945 -0.963 -0.967 -0.978 ...
##  $ V7  : num  -0.953 -0.987 -0.994 -0.995 -0.994 ...
##  $ V8  : num  -0.925 -0.968 -0.971 -0.974 -0.966 ...
##   [list output truncated]
```

### Part 2: Extract only the measurements on the mean and standard deviation for each measurement

For this part of the assignment, I had to identify which columns in the provided data set corresponded to measurements that I wanted to extract. With the help of the feature labels in the provided document *features.txt*, I determined the desired column indices. The assignment requested extract only **mean and standard deviation** values. Some items were obvious to select given their labels:

- 1 BodyAcc-mean()-X
- 2 tBodyAcc-mean()-Y
- 3 tBodyAcc-mean()-Z
- 4 tBodyAcc-std()-X
- 5 tBodyAcc-std()-Y
- 6 tBodyAcc-std()-Z

However, others were not so obvious:

- 294 fBodyAcc-meanFreq()-X (described as "mean" of frequency components)
- 295 fBodyAcc-meanFreq()-Y
- 296 fBodyAcc-meanFreq()-Z
- 297 fBodyAcc-skewness()-X
- 298 fBodyAcc-kurtosis()-X
- 299 fBodyAcc-skewness()-Y
- 300 fBodyAcc-kurtosis()-Y
- 301 fBodyAcc-skewness()-Z
- 302 fBodyAcc-kurtosis()-Z
- 559 angle(X,gravityMean)
- 560 angle(Y,gravityMean)
- 561 angle(Z,gravityMean)

Given the ambiguity in the instructions, I included columns for "meanFreq" items (since it is still a 'mean' measure), but I excluded the "skewness" and "kurtosis" items, since the latter two items are related to the shape of a distribution and not to standard deviation, strictly speaking. I also excluded the angles, since the
measured value itself does not appear to be a mean.

The *itemstoextract* variable is a list that stores all of the indices of the features to keep from the **original** dataset. This list was then used to determine which columns to extract from the newly created merged dataset.


```r
## identify columns in original *.x files to extract
itemstoextract <- list(1,2,3,4,5,6,41,42,43,44,45,46,81,82,83,84,85,86,121,122,123,124,125,126,161,162,163,164,165,166,201,202,214,215,227,228,240,241,253,254,266,267,268,269,270,271,294,295,296,345,346,347,348,349,350,373,374,375,424,425,426,427,428,429,452,453,454,503,504,513,516,517,526,529,530,539,542,543,552)

## since our merged data set has two columns at the beginning
## we need to extract the columns of data using column indices 
## adjusted by 2, and then also extract the first two columns
## (subject & activity)
addtwo <- as.list(rep(2,length(itemstoextract)))
extractfromMerge <- mapply(function(x1,y1) x1[[1]]+y1[[1]], itemstoextract, addtwo)
extractfromMerge <- as.list(c(1,2,extractfromMerge))

## change variable names of first two columns (subject, activity)
## to avoid errors with duplicate column names
names(mergeddataset)[1] <- "subjectID"
names(mergeddataset)[2] <- "activityID"

## extract the columns and save in new data frame
extractedData <- select(mergeddataset,extractfromMerge)

## preview details (commented in script)
str(extractedData, list.len=10)
```

```
## 'data.frame':	10299 obs. of  81 variables:
##  $ subjectID : int  2 2 2 2 2 2 2 2 2 2 ...
##  $ activityID: int  5 5 5 5 5 5 5 5 5 5 ...
##  $ V1        : num  0.257 0.286 0.275 0.27 0.275 ...
##  $ V2        : num  -0.0233 -0.0132 -0.0261 -0.0326 -0.0278 ...
##  $ V3        : num  -0.0147 -0.1191 -0.1182 -0.1175 -0.1295 ...
##  $ V4        : num  -0.938 -0.975 -0.994 -0.995 -0.994 ...
##  $ V5        : num  -0.92 -0.967 -0.97 -0.973 -0.967 ...
##  $ V6        : num  -0.668 -0.945 -0.963 -0.967 -0.978 ...
##  $ V41       : num  0.936 0.927 0.93 0.929 0.927 ...
##  $ V42       : num  -0.283 -0.289 -0.288 -0.293 -0.303 ...
##   [list output truncated]
```

### Part 3: Use descriptive activity names to name the activities in the dataset

Currently, the column that was renamed *activityID* stores the activity labels, which have values taken from the set {1, 2, 3, 4, 5, 6}. I searched through this column and substituted the number for the actual name of the activity, as provided in the documentation included with the original dataset.


```r
## perform search and replace within activityID column
extractedData$activityID <- gsub(1,"walking",extractedData$activityID)
extractedData$activityID <- gsub(2,"walking upstairs",extractedData$activityID)
extractedData$activityID <- gsub(3,"walking downstairs",extractedData$activityID)
extractedData$activityID <- gsub(4,"sitting",extractedData$activityID)
extractedData$activityID <- gsub(5,"standing",extractedData$activityID)
extractedData$activityID <- gsub(6,"laying",extractedData$activityID)

## preview changes (commented in script)
table(extractedData$activityID)
```

```
## 
##             laying            sitting           standing 
##               1944               1777               1906 
##            walking walking downstairs   walking upstairs 
##               1722               1406               1544
```

### Part 4: Appropriately label the dataset with descriptive variable names

This required me to analyze each selected column and choose an appropriate name -- a tedious task. I wrote a separate internal function **namevariables()** to do this. Refer to the R code for specific details. The resulting dataset is the "clean" data set, including data extracted from the raw data provided, and with activity labels and variables renamed.




```r
cleandata <- namevariables(extractedData)

## preview details (commented in script)
str(cleandata, list.len=10)
```

```
## 'data.frame':	10299 obs. of  81 variables:
##  $ subjectID                                      : int  2 2 2 2 2 2 2 2 2 2 ...
##  $ activityID                                     : chr  "standing" "standing" "standing" "standing" ...
##  $ mean body acceleration X axis                  : num  0.257 0.286 0.275 0.27 0.275 ...
##  $ mean body acceleration Y axis                  : num  -0.0233 -0.0132 -0.0261 -0.0326 -0.0278 ...
##  $ mean body acceleration Z axis                  : num  -0.0147 -0.1191 -0.1182 -0.1175 -0.1295 ...
##  $ std. dev. body acceleration X axis             : num  -0.938 -0.975 -0.994 -0.995 -0.994 ...
##  $ std. dev. body acceleration Y axis             : num  -0.92 -0.967 -0.97 -0.973 -0.967 ...
##  $ std. dev. body acceleration Z axis             : num  -0.668 -0.945 -0.963 -0.967 -0.978 ...
##  $ mean gravity acceleration X axis               : num  0.936 0.927 0.93 0.929 0.927 ...
##  $ mean gravity acceleration Y axis               : num  -0.283 -0.289 -0.288 -0.293 -0.303 ...
##   [list output truncated]
```

### Part 5: From the data set in step 4, create a second, independent tidy data set with the average of each variable for each activity and each subject

I grouped the data in the *cleandata* dataset by subject and activity, and then calculated the average value of the each data item for each group. I also renamed each variable name by adding the prefix "GroupAvg" to the previously re-named variables,
to emphasize that the variables in the new data set are derived group averages. The resulting data set was stored in *tidydata2*.


```r
## group by both subjectID and activityID
## then calculate mean, for each variable by group
tidydata2 <- group_by(cleandata, subjectID, activityID)
tidydata2 <- summarise_each(tidydata2, funs(mean), -subjectID, -activityID)

## add prefix "GroupAvg" to variable names to identify values as group averages
colnames(tidydata2) <- paste("GroupAvg", colnames(tidydata2), sep=":")
names(tidydata2)[1] <- "subjectID"   ## reset first column header
names(tidydata2)[2] <- "activityID"  ## reset second column header

## preview details
str(tidydata2, list.len=10)
```

```
## Classes 'grouped_df', 'tbl_df', 'tbl' and 'data.frame':	180 obs. of  81 variables:
##  $ subjectID                                               : int  1 1 1 1 1 1 2 2 2 2 ...
##  $ activityID                                              : chr  "laying" "sitting" "standing" "walking" ...
##  $ GroupAvg:mean body acceleration X axis                  : num  0.222 0.261 0.279 0.277 0.289 ...
##  $ GroupAvg:mean body acceleration Y axis                  : num  -0.04051 -0.00131 -0.01614 -0.01738 -0.00992 ...
##  $ GroupAvg:mean body acceleration Z axis                  : num  -0.113 -0.105 -0.111 -0.111 -0.108 ...
##  $ GroupAvg:std. dev. body acceleration X axis             : num  -0.928 -0.977 -0.996 -0.284 0.03 ...
##  $ GroupAvg:std. dev. body acceleration Y axis             : num  -0.8368 -0.9226 -0.9732 0.1145 -0.0319 ...
##  $ GroupAvg:std. dev. body acceleration Z axis             : num  -0.826 -0.94 -0.98 -0.26 -0.23 ...
##  $ GroupAvg:mean gravity acceleration X axis               : num  -0.249 0.832 0.943 0.935 0.932 ...
##  $ GroupAvg:mean gravity acceleration Y axis               : num  0.706 0.204 -0.273 -0.282 -0.267 ...
##   [list output truncated]
##  - attr(*, "vars")=List of 1
##   ..$ : symbol subjectID
##  - attr(*, "drop")= logi TRUE
```

Refer to the Codebook for descriptions of the variables in this dataset.

I believe this dataset is considered *tidy* since it satisfies the following requirements (see p. 4 of Wickham, Hadley: *Tidy Data* at http://vita.had.co.nz/papers/tidy-data.pdf): 

- Each variable forms a column.
- Each observation forms a row (each set of data was collected for a particular subject doing a particular activity).
- Each type of observational unit forms a table (if there were further details that had to be repeated for each subject, we might have considered separating out those details in a different table).

I note that the fixed variables are also shown before the measured variables, which should make the data set easier to understand.

### Submission 

Finally, the new tidy data set, *tidydata2*, was written to a file for subsequent reading. 


```r
write.table(tidydata2, file="tidydata2.txt", row.names=FALSE)
```

This file can be read into R using a standard read.table() command (for data with headers) when the file is in the current working directory:


```r
data <- read.table("tidydata2.txt",header=TRUE)
```
