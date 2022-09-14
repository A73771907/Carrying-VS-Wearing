# Carrying vs Wearing
## Understanding Step Count Differences Between Wearables and Smartphones

### Data

Data are included as three versions: Raws, Minute, and Bout.
- Raws incude raw step count data for each user and each user are saved as \[UID\].csv
- Minute include minute level step count data, and wearable steps and phone steps of each minute are saved.
- Bout include bout level step count data, which has column as bout type, wearable steps, phone steps, steps(average for both bouts), and duration.

Moreover, device profile for all participant can be found on device_type.csv and demographics from meta.csv.

### Preprocessing

All the codes used to make above preprocessed data are included in the Preprocess folder.
- unzip.py: It was used for unzipping the participants' data which is recieved as .zip format.
- proprocess.py: extracting raw step count, device profile, and demogrphics from the participants' data.<br> It was done for removing information that could threat the privacy concerns.
- bout.py: From raw step count data, minute-level step count data and bout-level step count data have been made using this code.

### Experiments

All the codes for analysis was can be found here.
clustering analysis and exploratory data analysis have been done using ipython shells, and multi-lvel regression was done using R.