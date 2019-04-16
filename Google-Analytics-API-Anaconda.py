# -*- coding: utf-8 -*-
"""
Created on Thu Jan 17 10:50:38 2019

@author: Pierre
"""
#############################################################
# Chargement des bibliothèques utiles et positionnement dans 
# le bon répertoire
#############################################################
#def main():   #on ne va pas utiliser le main car on reste dans Spyder
import matplotlib.pyplot as plt  #pour les graphiques
from pandas.plotting import register_matplotlib_converters #pour les dates dans les graphiques
register_matplotlib_converters()
import pandas as pd  #pour les Dataframes ou tableaux de données
import seaborn as sns #graphiques étendues


#pour le chemin courant
import os
print(os.getcwd())  #verif
#forcer mon répertoire sur ma machine - nécessaire quand on fait tourner le programme 
#par morceaux dans Spyder et que l'on n'a pas indiqué le répertoire en haut à droite.
#myPath = "C:/Users/MyUSERNAME/myPATH"
#os.chdir(myPath) #modification du path
#print(os.getcwd()) #verif


#
#
###############################################################################
#Code inspiré de  Hello Analytics API fourni par Google qui va nous aider 
#pour se connecter à l'API De Google Analytics 
# infos sur le sujet 
#https://developers.google.com/analytics/devguides/reporting/core/v4/quickstart/installed-py


import argparse #module d’analyse de ligne de commande

#pour se connecter
from apiclient.discovery import build
import httplib2
from oauth2client import client
from oauth2client import file
from oauth2client import tools
#from oauth2client.service_account import ServiceAccountCredentials  

#Les Mauvais clients (pas la peine de les copier - prenez les votres)
MYCLIENTID = "XXXXXXXXX-qb0pgbntdmvf32i1kni67u2o455t0rbh.apps.googleusercontent.com" 
MYCLIENTSECRET =    "Mi_JcEQRuBgOLHDj8MH_s0uw" 

SCOPE  = ['https://www.googleapis.com/auth/analytics.readonly']

# Analyse des arguments de ligne de commande
parser = argparse.ArgumentParser(formatter_class=argparse.RawDescriptionHelpFormatter, 
                                 parents=[tools.argparser])
flags = parser.parse_args([])

# Créer un objet flow pour connection oAuth
flow = client.OAuth2WebServerFlow(client_id=MYCLIENTID,
                           client_secret=MYCLIENTSECRET,
                           scope='https://www.googleapis.com/auth/analytics.readonly')
  


# Prepare credentials, and authorize HTTP object with them.
# If the credentials don't exist or are invalid run through the native client
# flow. The Storage object will ensure that if successful the good
# credentials will get written back to a file.
storage = file.Storage('analyticsreporting.dat')
credentials = storage.get()
if credentials is None or credentials.invalid:
  credentials = tools.run_flow(flow, storage, flags)
http = credentials.authorize(http=httplib2.Http())



#Analytics V3 pour la liste des comptes et récupération des View_ID
analyticsV3 = build('analytics', 'v3', http=http)
accounts = analyticsV3.management().accounts().list().execute()
total_accounts = accounts.get('totalResults')
for i in range(0,total_accounts) :
    account = accounts.get('items')[i].get('id')
    properties = analyticsV3.management().webproperties().list(
        accountId=account).execute()
    total_properties = properties.get('totalResults')
    for j in range(0,total_properties) : 
        property = properties.get('items')[j].get('id')
        profiles = analyticsV3.management().profiles().list(accountId=account,webPropertyId=property).execute() 
        total_profiles = profiles.get('totalResults')
        for k in range(0,total_profiles) :
            print("Site:"+profiles.get('items')[k].get('websiteUrl')+" Vue:"+profiles.get('items')[k].get('name')+" ID de Vue:"+profiles.get('items')[k].get('id'))
              
#on prend l'ID De vue vue qui nous intéresse pour nous le premier 
VIEW_ID = '47922230'              
              
####################### 

#######################################################################    
#Transformation de la réponse Google Analytics au format dataframe
#voir ici : 
#https://www.themarketingtechnologist.co/getting-started-with-the-google-analytics-reporting-api-in-python/
          
def dataframe_response(response):
  list = []
  # get report data
  for report in response.get('reports', []):
    # set column headers
    columnHeader = report.get('columnHeader', {})
    dimensionHeaders = columnHeader.get('dimensions', [])
    metricHeaders = columnHeader.get('metricHeader', {}).get('metricHeaderEntries', [])
    rows = report.get('data', {}).get('rows', [])
    
    for row in rows:
        # create dict for each row
        dict = {}
        dimensions = row.get('dimensions', [])
        dateRangeValues = row.get('metrics', [])

        # fill dict with dimension header (key) and dimension value (value)
        for header, dimension in zip(dimensionHeaders, dimensions):
          dict[header] = dimension

        # fill dict with metric header (key) and metric value (value)
        for i, values in enumerate(dateRangeValues):
          for metric, value in zip(metricHeaders, values.get('values')):
            #set int as int, float a float
            if ',' in value or '.' in value:
              dict[metric.get('name')] = float(value)
            else:
              dict[metric.get('name')] = int(value)

        list.append(dict)
    
    df = pd.DataFrame(list)
    return df
######################################################################



#########################################################################
# RECUPERATION DES DONNEES
##########################################################################
#Pages Vues sur toutes les années précédentes Trafic Brut 
def get_gaAllYears(analyticsV4, VIEW_ID):
  # Use the Analytics Service Object to query the Analytics Reporting API V4.
  return analyticsV4.reports().batchGet(
      body={
        'reportRequests': [
        {
          'viewId': VIEW_ID,
          'pageSize': 10000,  #pour dépasser la limite de 1000
          'dateRanges': [{'startDate': "2011-07-01", 'endDate': "2018-12-31"}],
          'metrics': [{'expression': 'ga:pageviews'}],
          'dimensions': [{'name': 'ga:date'}],
        }]
      }
  ).execute()

    
# Build the service object. en version V4 de Google Analytics API
analyticsV4 = build('analytics', 'v4', http=http)

response = get_gaAllYears(analyticsV4, VIEW_ID)  #récupération des données de Google Analytics

#Données récupérées de GA
gaAllYears = dataframe_response(response) #on récupère la réponse brute en dataframe.
#creation de la variable Année à partir de ga:date
gaAllYears['Année'] = gaAllYears['ga:date'].astype(str).str[:4]
#changement des noms de colonnes ga:date et ga:pageviews car le ":" gêne
#pour manipuler les colonnes.
gaAllYears = gaAllYears.rename(columns={'ga:date': 'date', 'ga:pageviews': 'pageviews'})
#transformation date string en datetime 
gaAllYears.date = pd.to_datetime(gaAllYears.date,  format="%Y%m%d")
#verifs
gaAllYears.dtypes
gaAllYears.count()  #2668 enregistrements 
gaAllYears.head(20)



##########################################################################
#Graphique avec des années de différentes couleurs.
sns.set()  #paramètres esthétiques ressemble à ggplot par défaut.
fig, ax = plt.subplots()  #un seul plot
sns.lineplot(x='date', y='pageviews', hue='Année', data= gaAllYears, 
                  palette=sns.color_palette("husl",n_colors=8))
fig.suptitle('Il semble y avoir une anomalie en fin 2016.', fontsize=14, fontweight='bold')
ax.set(xlabel='Année', ylabel='Nombre de pages vues par jour',
       title='le trafic est bien au dessus du reste des observations.')
fig.text(.3,-.03,"Nombre de pages vues par jour depuis 2011 - Données brutes", 
         fontsize=9)
plt.legend(bbox_to_anchor=(1.05, 1), loc=2, borderaxespad=0.)
#plt.show()
fig.savefig("PV-s2011.png", bbox_inches="tight", dpi=600)


##################################################################
# moyenne mobile
##########################################################################
#Graphique Moyenne Mobile 30 jours.
#calcul de la moyenne mobile sur 30 jours
gaAllYears['cnt_ma30'] =  gaAllYears['pageviews'].rolling(window=30).mean()

sns.set()  #paramètres esthétiques ressemble à ggplot par défaut.
fig, ax = plt.subplots()  #un seul plot
sns.lineplot(x='date', y='cnt_ma30', hue='Année', data= gaAllYears, 
                  palette=sns.color_palette("husl",n_colors=8))
fig.suptitle("L'anomalie fin 2016 est bien visible.", fontsize=14, fontweight='bold')
ax.set(xlabel='Année', ylabel='Nbre pages vues / jour en moyenne mobile',
       title='le trafic est bien au dessus du reste des observations.')
fig.text(.9,-.05,"Nombre de pages vues par jour depuis 2011 en moyenne mobile sur 30 jours \n Données brutes", 
         fontsize=9, ha="right")
plt.legend(bbox_to_anchor=(1.05, 1), loc=2, borderaxespad=0.)
#plt.show()
fig.savefig("PV-s2011-Moyenne-Mobile.png", bbox_inches="tight", dpi=600)

#on reste dans l'IDE
#if __name__ == '__main__':
#  main()

