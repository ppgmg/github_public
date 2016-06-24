# Project Repository

This repository contains code and documentation for projects created primarily
in the course of my studies.

## Data Engineering

[Go to repo](https://github.com/ppgmg/insight_hll) 

For the Insight Data Engineering Fellow program, I implemented a framework for testing the accuracy and efficiency of the HyperLogLog algorithm on real-time, streaming data. This algorithm allows for extremely quick computations of unique items in a data stream. I designed and built a pipeline in which simulated data was ingested using Apache Kafka and processed in real-time using Spark Streaming (program in Scala) atop a Hadoop/HDFS framework hosted on Amazon Web Services (AWS). 

## Data Science

### iSAX
(**Python**) I implemented an algorithm and accompanying tree structure to facilitate
the performance of fast similarity searches between time series (e.g. stock
prices), for integration into a
[database](https://github.com/Mynti207/cs207project)
*(for Harvard CS207: Systems
Development for Computational Science, May 2016)*.

### mastermind
(**Python**) I implemented several algorithms for solving high-dimensional versions
of the classic game, MasterMind, including exhaustive search algorithms and a
local optimization algorithm (simulated annealing). I also created a [video
presentation](https://youtu.be/9VpXru8dRGA) for the
[project](https://github.com/dominedo/am207project)
*(for Harvard AM207: Stochastic Methods for Data Analysis, Inference, and
  Optimization, May 2016)*.

### chess
(**R**) I implemented a variety of statistical and machine learning models
to predict, based on anonymized membership data, whether a member of US chess
would allow their membership to lapse a short time after joining. Predictive
performance was judged through an in-class
[Kaggle competition] (https://inclass.kaggle.com/c/lapsed-uschess-memberships)
in which we placed first
*(for Harvard STAT149: Statistical Sleuthing through Generalized Linear
  Models, May 2016)*.

### monkey
(**Python**) We built an autonomous agent that used reinforcement learning
(e.g. Q-learning) techniques to learn to play an arcade-style game.
*(for Harvard CS181: Machine Learning, April 2016)*.

### topics
(**Python**) As a short exercise in exploring topic modeling, I
implemented Latent Dirichlet Allocation to determine the topic of a set of
documents based on analysis of their words. The dataset included over
5 million document-word count pairings.
*(for Harvard CS181: Machine Learning, April 2016)*.

### tweets
(**Python**) I wrote code that calculates the average degree of a vertex
in a Twitter hashtag graph for the last 60 seconds, and updates this each time
a new tweet appears. The average degree is thus calculated over a 60-second
sliding window. This was written in response to a
[coding challenge](https://github.com/GeneDer/coding-challenge)
as part of an application to the
[Insight Data Engineering fellowship](http://insightdataengineering.com)
program *(April 2016)*.

### music
(**Python, scikitlearn**) We used machine learning methods to predict the
number of times different users will listen to tracks by different artists
over a given time horizon. Our analysis was based
on: basic demographic attributes that were provided for most of the 233K users, attributes for the
2K artists that were scraped from MusicBrainz and Wikipedia, and a
training set of the historical
number of plays of 4.1M user-artist pairs.
*(for Harvard CS181: Machine Learning, March 2016)*.

### virus
(**Python, scikitlearn**) We used machine learning methods to identify classes
of malware (or the lack of malware) in executable files. Our analysis was based
on XML logs of the executables’ execution histories, which we parsed in order
to create features associated with particular malware classes. Predictive
performance was judged through an in-class
[Kaggle competition] (https://inclass.kaggle.com/c/cs181-s16-classifying-malicious-software)
in which we placed fifth
*(for Harvard CS181: Machine Learning, March 2016)*.

### smiles
(**Python, R**) We built linear regression and random forest models to
predict the potential
efficiency of different molecules as building blocks for solar cells,
based on molecular structures encoded in the form of SMILES strings.
Predictive performance was judged through an in-class
[Kaggle competition] (https://inclass.kaggle.com/c/cs181-s16-practical-1-predicting-the-efficiency-of-photovoltaic-molecules)
in which we placed fifth
*(for Harvard CS181: Machine Learning, February 2016)*.

### digits
(**Python**) As a short exercise in exploring clustering algorithms, I
implemented the K-means algorithm from scratch to group similar images of
handwritten digits from the MNIST dataset
*(for Harvard CS181: Machine Learning, February 2016)*.

### bloom
(**C**) As a short exercise in exploring hashing methodologies, I
implemented a Bloom filter in C *(for Harvard CS207: Systems
Development for Computational Science, February 2016)*.

### montecarlo
(**Python, PyMC**) Solutions to some interesting homework exercises
applying stochastic methods to a variety of applications
*(for Harvard AM207: Stochastic Methods for Data Analysis, Inference, and
  Optimization, January-April 2016)*.

### spell
(**Python, Spark**) I implemented a Python port of Wolf Garbe's
["Symmetric Delete" algorithm](https://github.com/wolfgarbe/symspell), and
an adaptation using Apache Spark, to correct the spelling of text.
We also created a [video presentation and website](http://spark-n-spell.com)
for the [project](https://github.com/dominedo/spark-n-spell)
*(for Harvard CS205: Computing Foundations for Computational Science,
  December 2015)*.

### STEMwomen
(**Python, scikitlearn, Tableau**) We analyzed census microdata to investigate
gender imbalance in college STEM studies, through the application of analytical
and modeling techniques. Illustrations created using Tableau. We also created a
[video presentation and website](https://stemstudy.wordpress.com)
for the [project](https://github.com/ppgmg/stem-study)
*(for Harvard AC209: Data Science, December 2015)*.

### particles
(**Python, Cython**) As a short exercise in employing parallelism techniques,
I modified code for a physics simulator and animation system, and wrote a
short presentation for a seminar class describing my modifications
*(for Harvard CS205: Computing Foundations for Computational Science,
  November 2015)*.

### terror
(**Python, pandas**) Using Pandas to clean country data from multiple sources
to construct a data analysis for further analysis in a final project
*(for Harvard STAT139: Statistical Sleuthing using Linear Models,
  November 2015)*.

### spark_probs
(**Python, Spark**) Solutions to some interesting homework exercises
utilizing Apache Spark
*(for Harvard CS205: Computing Foundations for Computational Science,
  October 2015)*.

### datasci_probs
(**Python, scikitlearn**) Summary of Data Science homework exercises completed
*(for Harvard AC209: Data Science, October-November 2015)*.

### coursera
(**R**) Select projects from Coursera's Data Science specialization *(2014)*
