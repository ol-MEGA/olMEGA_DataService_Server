# todo list for data analysis of IHAB data

## OVD 
1) Feature Extraktor OVD based an Jules ideas (Python ML (scikit-learn) or transplant)


## Feature Analyzer

### OVD based on the ovd files

### Band energy as a new feature file 

Parameters:
* time base: 0.125s or 1s
* freq resolution : octav, third-octave, mel via matrix operation
    form of bands and band cutting (rectangularStrict (no dividing of energy in one band)), rectangularlineardivided, triangle, IEC )

Frequencies from 125 Hz to 4kHz

### Band energy as a new feature
FFT to band is solved
time base 60s 
mean and std of 0.125s blocks 5, 50 median and 95% percentile per frequency band 

Parameters:
* freq resolution

### LEQ (a weighted (?))



### searchable statistics (5% and 95% percentiles)

### psychoacoustical measures

### SoundScape Features


## Client-Tool (https://github.com/ol-MEGA/olMEGA_DataService_Client)

### List of typical problems


zunächst also zu den Fragen bzw. Fragekomplexen, die ich für die objektiven EMA-Daten insbesondere in Verbindung mit den Fragebogenbewertungen sehe. Ich versuche allgemein zu bleiben, konkrete Parameter etc. wollten wir ja in weiteren Schritten vereinbaren.

*1*: Beziehung zwischen akustisch-physikalischen Größen (bzw. darauf basierender Parameter), Kontextinformationen (zB Situation, Aktivität, Tageszeit) und den subjektiven Bewertungen (zB Lautheit, Fähigkeit der Richtungserkennung, Angenehmheit, Höranstrengung). Was ist mit was assoziiert - da wird explorativ wohl am meisten stattfinden.

Eine konkrete Frage wäre zB wie stark der Kontext/Situation bzw. mit der Situation verbundene Erwartungen die Lautheitsbewertung auf der verwendeten 7-stufigen Kategorialskala beeinflusst. (Gilt z.B. außer Haus eine Umgebung als leise, die zu Hause als „mittel“ beurteilt wird?)

*2*: Wie sieht der akustische Alltag der Studienteilnehmer aus? Lassen sich in den EMA-Daten unterschiedliche Profile erkennen? Wenn deutliche Unterschiede bestehen: Sind diese auf einen unterschiedlichen Mix von Szenarien oder eher auf unterschiedliche Ausprägungen gleicher Szenarien zurückzuführen?

Konkret wäre das zB ein Vergleich individueller EMA-Daten nach der Verteilung von Pegelparametern für die gesamte EMA-Phase oder ausgewählte Situationen.

*3:* Für die Beurteilung der Compliance und der Auswertung i.Allg. interessieren Meta-Daten zu der Erfassung der objektiv-akustischen Parameter. Wie lange war das System aktiv? Oder im optimalen Fall: Wie lange wurde es getragen? Uhrzeiten Beginn, Ende und längere Unterbrechungen (> 30 min oder so? nicht die immer wieder auftretenden Kontaktunterbrechungen).

Konkret habe ich bislang die tägliche Dauer der EMA nach dem ersten und letzten Survey des Tages bemessen. Die Compliance wurde u.a. mit diesem Bezug errechnet. Möglicherweise stellt sich diese Kennzahl in manchen Fällen ganz anders dar, wenn die Laufzeit des Systems betrachtet wird.

*4:* Je länger die bewerteten Situationen zurückliegen, desto unsicherer wird wohl die richtige Auswahl von Zeitabschnitten. Von Interesse sind deshalb übersichtliche Parameter oder eine rudimentäre Situationserkennung, die zumindest abschätzen lassen, ob bzw. in welchem Maß die PSDs der gewählten Zeitabschnitte stimmig mit den Fragebogenangaben sind.

Konkret zB ob bei der Angabe von Radio oder einer Verkehrssituation die gewählten Abschnitte auch typische Merkmale von Musik oder Motorengeräusch enthalten. %-OV dürfte einfach beizubringen sei, hält also für Kommunikationssituationen. Aber sonst?

*5*: Den Effekt der OVD für die Pegelschätzung würde ich für ausgewählte Situationen untersuchen und ggf. mit Anschluss an andere Veröffentlichungen diskutieren wollen. Global ist dies ja schon im OVD-Manuskript geschehen, zumindest in der Version, die ich kenne. Dabei geht es nicht nur darum, wieviel dB mehr oder weniger rauskommen.

Konkret wäre zB die Frage, ob die Pegelschätzungen mit OVD zB eine bessere Varianzaufklärung für die Lautheitsschätzung oder in einem komplexeren Modell für die klassischen Outcomes Höranstrengung, Sprachverstehen leisten als die Pegelschätzungen ohne OVD. 


### List of basic tools for databank analysis

### example files for different research questions





# Done


### RMS (a-weighted) via PSD
a-weighting as a new databank entry is solved

### band energy
FFT to band is solved
time base 60s mean is implemented