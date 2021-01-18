import mysql.connector


def getConnection():
    # step1: connect to MySQL Server
    # localhost = 127.0.0.1
    connection = mysql.connector.connect(host="127.0.0.1", user="root", password="NehalBandal@84", database="fifa18")

    # step2: Perform operation
    return connection


def getFile():
    connection = getConnection()
    cursor = connection.cursor()
    query = "SELECT file FROM uploaded_files ORDER BY upload_time DESC LIMIT 1 "
    cursor.execute(query)
    filename = cursor.fetchall()
    return filename


def convertToFloat(df_col):
    result = []
    units = {"K": 1000, "M": 1000000}
    for val in df_col:
        try:
            result.append(float(val))
        except ValueError:
            unit = val[-1]
            val = float(val[:-1])
            result.append(val * units[unit])

    return result


import numpy as np
import pandas as pd
import os
from unidecode import unidecode
from pandas.api.types import is_string_dtype
from sklearn.externals import joblib

name = getFile()
print(name)
# Step 1 : Read the dataset

readFile = pd.read_csv(name[0][0], low_memory=False)
# path = os.path.join(os.path.dirname(__file__), "upload/")
# readFile = pd.read_csv(path+"sample_6.csv")

columns = ['ID', 'Name', 'Age', 'Nationality', 'Potential', 'Club',
           'Value', 'Wage', 'Height_cm', 'Weight_kg', 'Acceleration', 'Aggression',
           'Agility', 'Balance', 'Ball control', 'Composure', 'Crossing', 'Curve',
           'Dribbling', 'Finishing', 'Free kick accuracy', 'GK diving',
           'GK handling', 'GK kicking', 'GK positioning', 'GK reflexes',
           'Heading accuracy', 'Interceptions', 'Jumping', 'Long passing',
           'Long shots', 'Marking', 'Penalties', 'Positioning', 'Reactions',
           'Short passing', 'Shot power', 'Sliding tackle', 'Sprint speed',
           'Stamina', 'Standing tackle', 'Strength', 'Vision', 'Volleys']

df = pd.DataFrame(readFile, columns=columns)
print("--------------------Step 1 DONE !!! ---------------------------")

# Step 2 : Convert accented characters to normal form.

df['Name'] = df['Name'].apply(lambda x: unidecode(str(x)))
df['Club'] = df['Club'].apply(lambda x: unidecode(str(x)))

df["Value"] = df["Value"].str.split('€').str.get(1)
df["Value"] = convertToFloat(df["Value"])
df["Wage"] = df["Wage"].str.split('€').str.get(1)
df["Wage"] = convertToFloat(df["Wage"])

print("--------------------Step 2 DONE !!! ---------------------------")

# Step 3 : Replace missing values

nan_cols = df.isna().sum()  # get columns which contain NaN values along with count
nan_cols = nan_cols.to_dict()
nan_cols = [key for key, value in nan_cols.items() if value != 0]
for col in nan_cols:
    df[col] = df[col].fillna(df[col].mean())

cat = ["Name", "Nationality", "Club"]
for var in cat:
    df[var] = df[var].fillna("unknown")
print("--------------------Step 3 DONE !!! ---------------------------")

# step 4 : make each observations in each column uniform and convert into appropriate data type
attrs = ['Acceleration', 'Aggression', 'Agility', 'Balance', 'Ball control', 'Composure',
         'Crossing', 'Curve', 'Dribbling', 'Finishing', 'Free kick accuracy',
         'GK diving', 'GK handling', 'GK kicking', 'GK positioning',
         'GK reflexes', 'Heading accuracy', 'Interceptions', 'Jumping', 'Long passing', 'Long shots',
         'Marking', 'Penalties', 'Positioning', 'Reactions', 'Short passing', 'Shot power',
         'Sliding tackle', 'Sprint speed', 'Stamina', 'Standing tackle', 'Strength', 'Vision', 'Volleys']

for attr in attrs:
    if is_string_dtype(df[attr]):
        df[attr] = df[attr].apply(lambda x: eval(x))

for attr in attrs:
    df[attr] = pd.to_numeric(df[attr])

print("--------------------Step 4 DONE !!! ---------------------------")

# Step 5 : Assign continent
path = os.path.join(os.path.dirname(__file__), "ml/Datasets/")
df_continent = pd.read_csv(path + 'country_continent.csv')

# Create a dictionary where key --> Country and Value --> Continent
newdict = {}
for value in list(range(len(df_continent))):
    newdict[df_continent.iloc[value, 0]] = df_continent.iloc[value, 1]

# assign continent to each player.
df['Continent'] = ""
for each in list(range(len(df))):
    df['Continent'][each] = newdict[df['Nationality'][each]]
print("--------------------Step 5 DONE !!! ---------------------------")

# Step 6 : Assign fieldPosition
pos_attrs = ['Acceleration', 'Aggression', 'Agility', 'Balance', 'Ball control', 'Composure', 'Crossing',
             'Curve', 'Dribbling', 'Finishing', 'Free kick accuracy', 'GK diving', 'Heading accuracy', 'Interceptions',
             'Jumping', 'Long passing', 'Long shots', 'Marking', 'Penalties', 'Positioning',
             'Reactions', 'Short passing', 'Shot power', 'Sliding tackle', 'Sprint speed', 'Stamina',
             'Standing tackle', 'Strength', 'Vision', 'Volleys']

df_attr = pd.DataFrame(df, columns=pos_attrs)
path = os.path.join(os.path.dirname(__file__), "ml/models/")
fieldPosition = joblib.load(path + 'field_position.pkl')
output_fieldPosition = fieldPosition.predict(df_attr)
df['FieldPositions'] = output_fieldPosition
print("--------------------Step 6 DONE !!! ---------------------------")

# Step 7 : Assign exactPosition
path = os.path.join(os.path.dirname(__file__), "ml/models/")
exactPosition = joblib.load(path + 'exact_position.pkl')
output_exactPosition = exactPosition.predict(df_attr)
df['Position'] = output_exactPosition
print("--------------------Step 7 DONE !!! ---------------------------")

# Step 8 : Calculate position wise overall
attrs.insert(0, "Age")
df_attr = pd.DataFrame(df, columns=attrs)
output_col = ['ST', 'CF', 'RF', 'LF', 'RW', 'LW', 'RS', 'LS', 'CAM', 'RAM', 'LAM', 'CM', 'RCM', 'LCM', 'LM', 'RM',
              'CDM', 'RDM', 'LDM'
    , 'CB', 'RB', 'LB', 'RCB', 'LCB', 'RWB', 'LWB']

for pos in output_col:
    name = path + pos + ".pkl"
    position_wise_overall = joblib.load(name)
    output_position_wise_overall = position_wise_overall.predict(df_attr)
    df[pos] = output_position_wise_overall

df[output_col] = df[output_col].astype('int')

print("--------------------Step 8 DONE !!! ---------------------------")

# Step 9 : Calculate strengths Atk Mid Def
attack = ['ST', 'CF', 'RF', 'LF', 'RW', 'LW', 'RS', 'LS']
midfield = ['CAM', 'RAM', 'LAM', 'CM', 'RCM', 'LCM', 'LM', 'RM', 'CDM', 'RDM', 'LDM']
defense = ['CB', 'RB', 'LB', 'RCB', 'LCB', 'RWB', 'LWB']

df['Atk'] = 0
df['Mid'] = 0
df['Def'] = 0

for i in list(range(0, len(df))):
    atk = df[attack].iloc[i].mean()
    mid = df[midfield].iloc[i].mean()
    defn = df[defense].iloc[i].mean()
    df['Atk'][i] = atk
    df['Mid'][i] = mid
    df['Def'][i] = defn
print("--------------------Step 9 DONE !!! ---------------------------")

# Step 10: Calculate overall
path = os.path.join(os.path.dirname(__file__), "ml/models/")
overall = joblib.load(path + 'overall.pkl')
output_overall = overall.predict(df_attr)
df['Overall'] = output_overall
df['Overall'] = df['Overall'].astype('int')
print("--------------------Step 10 DONE !!! ---------------------------")

# Step 11: Load Data in MySQL
from sqlalchemy import create_engine

engine = create_engine('mysql+mysqlconnector://root:NehalBandal@84@localhost:3306/fifa18', echo=False)

personal = ['ID', 'Name', 'Age', 'Nationality', 'Continent', 'Club', 'Wage', 'Value']
df_personal = pd.DataFrame(df, columns=personal)
df_personal.to_sql(name='player_personal_info', con=engine, if_exists='append', index=False)

physical = ['ID', 'Height_cm', 'Weight_kg', 'Acceleration', 'Aggression', 'Agility',
            'Balance', 'Ball control', 'Composure', 'Crossing', 'Curve',
            'Dribbling', 'Finishing', 'Free kick accuracy', 'GK diving',
            'GK handling', 'GK kicking', 'GK positioning', 'GK reflexes',
            'Heading accuracy', 'Interceptions', 'Jumping', 'Long passing',
            'Long shots', 'Marking', 'Penalties', 'Positioning', 'Reactions',
            'Short passing', 'Shot power', 'Sliding tackle', 'Sprint speed',
            'Stamina', 'Standing tackle', 'Strength', 'Vision', 'Volleys']
df_physical = pd.DataFrame(df, columns=physical)
df_physical.to_sql(name='player_physical_attrs', con=engine, if_exists='append', index=False)

positional = ['ID', 'CAM', 'CB', 'CDM', 'CF', 'CM', 'ID', 'LAM', 'LB', 'LCB', 'LCM', 'LDM',
              'LF', 'LM', 'LS', 'LW', 'LWB', 'RAM', 'RB',
              'RCB', 'RCM', 'RDM', 'RF', 'RM', 'RS', 'RW', 'RWB', 'ST']
df_positional = pd.DataFrame(df, columns=positional)
df_positional.to_sql(name='player_positional_attrs', con=engine, if_exists='append', index=False)

abstract = ['ID', 'Atk', 'Mid', 'Def', 'Overall', 'Potential', 'FieldPositions', 'Position']
df_abstract = pd.DataFrame(df, columns=abstract)
df_abstract.to_sql(name='player_abstract_info', con=engine, if_exists='append', index=False)
print("--------------------Step 11 DONE !!! ---------------------------")
