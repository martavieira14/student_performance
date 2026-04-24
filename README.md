# Student Insights & Analysis Dashboard
This project is an interactive web application built with Shiny for Python. It was developed to explore, clean, and analyze data related to student academic performance. The dashboard provides an interactive graphical interface that allows users to:

- Handle and impute missing values (NAs).
- View descriptive statistics and evaluate top/bottom performing groups.
- Explore univariate and bivariate graphs to understand relationships between student behaviors and their academic outcomes.
- Generate and download dynamic statistical reports and cleaned datasets.

The goal of this tool is to provide an end-to-end exploratory data analysis experience using a Student Performance dataset.

## Dataset
The application uses the open-source Student Performance Dataset from Kaggle, originally published by Nikhil Narayan.
Original dataset: 6 columns, 10 000 observations.
Variables: hours studied, sleep hours, previous scores, extracurricular activities, sample question papers practiced and performance index. 

It provides a foundation for analyzing how lifestyle and study metrics correlate with final academic performance.

## Features
1. **Data Overview & Cleaning**
Users can upload their CSV files, instantly view dataset shape/metadata, and manage missing values dynamically by choosing methods like Mean, Median, Mode, or Dropping rows. Download the cleaned CSV directly from the UI.

2. **Descriptive Statistics**
Configure a target variable (e.g., Performance Index) and select a percentage slice (e.g., Top 10% vs Bottom 10%). The app auto-generates comparative tables showing the mean/mode profiles of the best vs. worst-performing students. Downloadable as a .txt report.

3. **Interactive Visualizations**
Exploratory graphical analysis through dynamic charting built with Seaborn and Matplotlib.
- Univariate Analysis: Histograms, Q-Q Plots, Boxplots, Bar charts, and Pie charts (auto-adapting to numeric or categorical types).
- Bivariate Analysis: Regression plots, grouped boxplots, and stacked bar charts for cross-variable interactions.
- Correlation Heatmap: Automatically grabs numeric variables to display a correlation matrix.

## Instalation and requirements
The file environment.yml have all dependencies needed for this project:
```yaml
name: student_performance
channels:
  - conda-forge
  - defaults
dependencies:
  - python=3.12
  - pandas
  - numpy
  - matplotlib
  - seaborn
  - scipy
  - pip
  - pip:
    - shiny
```

### Conda
1. Clone the repository:
```
git clone https://github.com/martavieira14/student_performance.git
cd student_performance
```

2. Create Conda environment:
```
    conda env create -f environment.yml
    conda activate student_performance
```

3. Run the application:
```
    shiny run app.py 
```

## Contribution:
To contribute to this project:
1. Fork the repository.
2. Create a new branch: `git checkout -b my-branch`.
3. Commit your changes: `git commit -m 'changes'`.
4. Push to your branch: `git push origin my-branch`.
5. Open a pull request.

## Developers:
Developed by Marta Vieira, during master's degree in Clinical Bioinformatics.

University: Universidade de Aveiro – MSc in Clinical Bioinformatics.

## License
This project is licensed under the terms of the MIT License.

