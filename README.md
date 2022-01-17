# WDW History

I spent several years gathering data and building small tools to help with my research into the history of Walt Disney World, with a particular interest in maps and cartography. I no longer have enough interest in it to continue this work, so I'm dropping what I have so far in this repository, in case anyone else wants to pick up where I left off.

## Original Goals

There are a few specific things I was hoping to do at some point using this work. If any of this resonates with you, this repository might be useful. If not, maybe you can find your own uses for it. Or not. :shrug:

### Interactive map of Walt Disney World over time

Imagine a regular interactive map, but with a slider to select the date you want to view. This would basically be a localized equivalent to [Open Historical Map](https://openhistoricalmap.org/). But I couldn't guarantee that all the data for Walt Disney World would come from sources that meet the criteria for their license, I assumed I'd have to build a separate database.

### _A Cartographic History of Walt Disney World_

I had started to discover enough interesting stories, particularly about the pre-Disney history of the property, that I had wanted to write a book about it all, titled _A Cartographic History of Walt Disney World_. It would basically tell the stories of land ownership prior to Disney, lay out the process of Disney buying the land, and then showcase the changes that have taken place on the property in the 50+ years since Disney bought the land.

### "When was my vacation?"

This was more personal for me. I visited Walt Disney World a few times when I was young, but I don't remember much of it. My parents couldn't even tell me what years we went, so it was hard for me to figure out what attractions I might have experienced when I was young. The idea here would be to ask what attractions you do remember, and using the opening/closing dates to narrow down a time frame when those attractions were all open at the same time. Once you have a good idea when you visited (or if you already knew the dates), you could go back to the historical map to see what the property looked like, and what attractions you would've had access to. With any luck, that might trigger some more memories.

## Data Sources

I've gathered a few different data sources to work from over the years. This repo will contain the small portion of it that I've processed, but here's where it all comes from, so others can grab it themselves direct from each source.

### Aerial photography from the Florida Department of Transportation

### Notices of Commencement from the Orange County Comptroller's Office

### PLSS survey points from the Orange County Appraiser's Office

The property descriptions from the comptroller's office use the [Public Land Survey System (PLSS)](https://en.wikipedia.org/wiki/Public_Land_Survey_System), which requires a starting point for the property description. That point is referenced in the document, but not given latitude and longitude coordinates. The appraiser's office does have a database of those points. I've included a GeoJSON file in this repositority containing all the points needed for Walt Disney World, but there are also other datasets available from the appraiser's office that might prove useful.

The data is available an ArcGIS service, but it has a weird URL prefix that messes up the scripts I've thrown at it. Rather than try to manually munge the URLs and perhaps introduce more bugs, I found it similar to introduce a redirect service in front of it to simplify things. I've put the [redirector code](https://github.com/gulopine/redirector) in its own repository so that it's easier to deploy it directly to Heroku, for free. You'll need to sign up for a Heroku account, but the app doesn't use any resources that would require a credit card. This button will take you to a simple deployment screen.

[![Deploy](https://www.herokucdn.com/deploy/button.svg)](https://heroku.com/deploy?template=https://github.com/gulopine/redirector&env[INITIAL_REDIRECT]=/arcgis/rest/services/&env[REMOTE_BASE]=https://maps.ocpafl.org/Proxy/proxy.ashx?https://gisapp2.ocpafl.org)

### Building footprints from Microsoft

https://github.com/Microsoft/USBuildingFootprints

### Variety of information from ArcGIS collections

https://www.arcgis.com/home/search.html?q=rcid
https://www.arcgis.com/home/search.html?q=wdw

### Newspapers.com

