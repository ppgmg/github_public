# spark-n-spell README (Archive)

Note: This code is no longer being actively maintained. 

## EXECUTABLES

**Note:** All scripts were developed and tested using Python 2.7 and spark-1.5.0 and may not run as expected on other configurations.

### Word-Level Correction

(a) Run our Python port of SymSpell to correct *individual* words.

- download *symspell_python.py* to your local directory
- download the dictionary file *big.txt* to the same directory, from this github repository or one of the following additional sources: 
  - http://norvig.com/ngrams/ 
  - or use your own dictionary file renamed as *big.txt*
- at the prompt, run:  `python symspell_python.py`
- type in the word to be corrected at the interactive prompt

(b) Run our Spark program to correct *individual* words.

- download *symspell_spark.py* to your local directory (you should have Spark 1.5.0 installed, and you must be able to call spark-submit from that directory)
- if not already done, download the dictionary file *big.txt* from one of sources listed above
- at the prompt, run:  `spark-submit symspell_spark.py -w "<word to correct>"` 
  - e.g. `spark-submit symspell_spark.py -w "cvhicken"`

## DOCUMENTATION

Consult our IPYTHON NOTEBOOKS for documentation on our coding and testing process.
