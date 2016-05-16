Getting and Cleaning Data Course Project
========================================
submitted by: ppgmg

## CodeBook.md

The files constituting this assignment submission include:

- **run_analysis.R**: the script used to generate a new tidy data set with the average of each variable for each activity and each subject
- **tidydata2.txt**: the new tidy data set created with the script
- **README.md**: a README file detailing how the scripts work
- **CodeBook.md**: the current document

### Input Data

The script processes data from experiments carried out with a group of 30 volunteers within an age bracket of 19-48 years. Each person performed six activities (WALKING, WALKING_UPSTAIRS, WALKING_DOWNSTAIRS, SITTING, STANDING, LAYING) wearing a smartphone (Samsung Galaxy S II) on the waist. Using its embedded accelerometer and gyroscope, 3-axial linear acceleration and 3-axial angular velocity at a constant rate of 50Hz were captured. The dataset for these experiments were randomly partitioned into two sets, where 70% of the volunteers was selected for generating the training data and 30% the test data. 

The files in the provided raw data set from which data was loaded by the script include:

- 'test/X_test.txt': Test set.
- 'test/y_test.txt': Test labels. From the provided activity_labels.txt file, the labels take on the following values: 1 WALKING, 2 WALKING_UPSTAIRS, 3 WALKING_DOWNSTAIRS, 4 SITTING, 5 STANDING, 6 LAYING.
- 'test/subject_test.txt': Each row identifies the subject who performed the activity for each window sample. Its range is from 1 to 30. 

- 'train/X_train.txt': Training set.
- 'train/y_train.txt': Training labels. From the provided activity_labels.txt file, the labels take on the following values: 1 WALKING, 2 WALKING_UPSTAIRS, 3 WALKING_DOWNSTAIRS, 4 SITTING, 5 STANDING, 6 LAYING.
- 'train/subject_train.txt': Each row identifies the subject who performed the activity for each window sample. Its range is from 1 to 30.

For further information on this dataset, see:
http://archive.ics.uci.edu/ml/datasets/Human+Activity+Recognition+Using+Smartphones

### Merged Data Set

The script produces an intermediate data set from the raw data noted above. This data set is created by initially merging the original training and the test sets to create one data set (*mergeddataset*). Then, only measurements relating to a "mean" or "standard deviation" were retained, and the variable names and activity labels changed to be more descriptive. The resulting dataset was stored in a new data frame (*cleandata*). 

### Output: New Data Set (*tidydata2*)

The script produces a new data set with the average of each variable in the *cleandata* intermediate dataset, for each activity and each subject.

Note that the variables in *cleandata* include the following fixed variables:

- **subjectID**: subject identifier, range is 1 to 30
- **activityID**: activity performed when measurement was taken (walking, walking upstairs, walking downstairs, sitting, standing, laying) 

and the following measured or derived variables, with values intact from the original data set (with units as noted):

#### variables estimated from body (linear) acceleration measurements, axial components, time domain signals (units: g):

- **mean body acceleration X axis** 
- **mean body acceleration Y axis** 
- **mean body acceleration Z axis**
- **std. dev. body acceleration X axis**
- **std. dev. body acceleration Y axis**
- **std. dev. body acceleration Z axis**

#### variables estimated from gravity (linear) acceleration measurements, axial components, time domain signals (units: g):

- **mean gravity acceleration X axis**
- **mean gravity acceleration Y axis**
- **mean gravity acceleration Z axis**
- **std. dev. gravity acceleration X axis**
- **std. dev. gravity acceleration Y axis**
- **std. dev. gravity acceleration Z axis**

#### variables estimated from derived jerk values (third derivative of position), axial components, time domain signals (units: g/s):

- **mean jerk X axis**
- **mean jerk Y axis**
- **mean jerk Z axis**
- **std. dev. jerk X axis**
- **std. dev. jerk Y axis**
- **std. dev. jerk Z axis**

#### variables estimated from angular velocity measurements, axial components, time domain signals (units: radians/s):

- **mean angular velocity X axis**
- **mean angular velocity Y axis**
- **mean angular velocity Z axis**
- **std. dev. angular velocity X axis**
- **std. dev. angular velocity Y axis**
- **std. dev. angular velocity Z axis**

#### variables estimated from derived angular jerk values (second derivative of angular velocity), axial components, time domain signals (units: radians/s^3):

- **mean angular jerk X axis**
- **mean angular jerk Y axis**
- **mean angular jerk Z axis**
- **std. dev. angular jerk X axis**
- **std. dev. angular jerk Y axis**
- **std. dev. angular jerk Z axis**

#### variables estimated from magnitudes (i.e. of vector with X, Y, Z components) of measured or derived quantities noted above (using Euclidean norm):

- **mean body acceleration** (units: g)
- **std. dev. body acceleration** (units: g)
- **mean gravity acceleration** (units: g)
- **std. dev. gravity acceleration** (units: g)
- **mean jerk** (units: g/s)
- **std. dev. jerk** (units: g/s)
- **mean angular velocity** (units: radians/s)
- **std. dev. angular velocity** (units: radians/s)
- **mean angular jerk** (units: radians/s^3)
- **std. dev. angular jerk** (units: radians/s^3)

A Fast Fourier Transform (FFT) was applied when preparing the original data set, resulting in certain measured and derived quantities analogous to the above, but in the frequency domain.

#### variables estimated from body (linear) acceleration measurements, axial components, frequency domain signals (units: g):

- **mean body acceleration X axis freq. domain**
- **mean body acceleration Y axis freq. domain** 
- **mean body acceleration Z axis freq. domain**
- **std. dev. body acceleration X axis freq. domain**
- **std. dev. body acceleration Y axis freq. domain**
- **std. dev. body acceleration Z axis freq. domain**

weighted average of frequency components - units: Hz

- **wtd. avg. of freq. components body acc. X axis**
- **wtd. avg. of freq. components body acc. Y axis**
- **wtd. avg. of freq. components body acc. Z axis**

#### variables estimated from derived jerk values (third derivative of position), axial components, freq domain signals (units: g/s):

- **mean jerk X axis freq. domain**
- **mean jerk Y axis freq. domain**
- **mean jerk Z axis freq. domain**
- **std. dev. jerk X axis freq. domain**
- **std. dev. jerk Y axis freq. domain**
- **std. dev. jerk Z axis freq. domain**

weighted average of frequency components - units: Hz

- **wtd. avg. of freq. components jerk X axis**
- **wtd. avg. of freq. components jerk Y axis**
- **wtd. avg. of freq. components jerk Z axis**

#### variables estimated from angular velocity measurements, axial components, frequency domain signals (units: radians/s):

- **mean angular velocity X axis freq. domain**
- **mean angular velocity Y axis freq. domain**
- **mean angular velocity Z axis freq. domain**
- **std. dev. angular velocity X axis freq. domain**
- **std. dev. angular velocity Y axis freq. domain**
- **std. dev. angular velocity Z axis freq. domain**

weighted average of frequency components - units: Hz

- **wtd. avg. freq. components ang. velocity X axis**
- **wtd. avg. freq. components ang. velocity Y axis**
- **wtd. avg. freq. components ang. velocity Z axis**

#### variables estimated from magnitudes (i.e. of vector with X, Y, Z components) of measured or derived quantities, in the frequency domain, noted above (using Euclidean norm):

- **mean body acceleration freq. domain** (units: g)
- **std. dev. body acceleration freq. domain** (units: g)
- **wtd. avg. freq. components body acc.** (units: Hz)
- **mean jerk freq. domain** (units: g/s)
- **std. dev. jerk freq. domain** (units: g/s)
- **wtd. avg. freq. components jerk** (units: Hz)
- **mean angular velocity freq. domain** (units: radians/s)
- **std. dev. angular velocity freq. domain** (units: radians/s)
- **wtd. avg. freq. components angular velocity** (units: Hz)

*note*: no separate quantities were provided for the X, Y, Z components of angular jerk in the frequency domain; however, the magnitudes were provided

- **mean angular jerk freq. domain** (units: radians/s^3)
- **std. dev. angular jerk freq. domain** (units: radians/s^3)
- **wtd. avg. freq. components angular jerk** (units: Hz)

From *cleandata*, a new tidy data set was created:

*tidydata2*: data frame storing average of each variable for each activity and each subject (30 subjects x 6 activities = 180 rows, 81 variables)

The columns of this new dataset represent calculated **averages** for each variable noted above (in the clean dataset), grouped by subject and activity. 

In order to distinguish these computed averages from the measured and derived quantities in the source dataset, **each of the variable names has been modified to include the *GroupAvg:* prefix in the new dataset**, and the reader is directed to the foregoing descriptions for the base variables from which the averages were computed, for further details.

Please see the README file for details regarding the transformations or work performed by the script to clean up the input data.
