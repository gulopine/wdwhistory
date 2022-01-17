## Data Sources

I've gathered a few different data sources to work from over the years. This repo will contain the small portion of it that I've processed, but here's where it all comes from, so others can grab it themselves direct from each source.

### OpenStreetMap

I'm going to start right off with some controversy. [OpenStreetMap](https://openstreetmap.org/) already has a lot of great data about the current state of WDW. But there are two potential problems with using them as a data source for any of these projects:

1. Their data is up-to-date, which not only means it can change out from under you, it means that it doesn't contain any historical information. In order to make it useful for historical mapping, you'd have to make a copy of it to your own database and augment the data with date/time information and then add in all the historical details alongside the modern pieces.
2. That new database you create would then be a derivative work, bound by [OpenStreetMap's copyright licensing](https://www.openstreetmap.org/copyright). In addition to attributing OpenStreetMap contributors (which I wholeheartedly support, being one of them myself), it would also mean your new database would be bound by the terms of the [Open Database License](https://opendatacommons.org/licenses/odbl/) as well.

If none of that deters you, great! Have fun starting with a rich dataset that you can build on. If not, you'll have to recreate all that data the old-fashioned way, from whatever sources the OpenStreetMap mappers used in the first place. In my experience, that was mostly tracing aerial photography, labeling buildings from firsthand knowledge, taking my own pictures of bus stops and bathhroom locations and finding open-licensed images on Flickr when I didn't have any of my own.

### Aerial photography from the Florida Department of Transportation (FDOT)

FDOT maintains a historical record of aerial photograpy dating back nearly a hundred years. It's a great resource for the placement of features that no longer exist, and the resolution of the images is high enough that they can be traced reasonably well. They don't have imagery for every county for every year, though, so it can be a bit hit and miss if you're looking for something that wasn't around for very long.

[FDOT Aerial Photography](https://www.fdot.gov/gis/aerialmain.shtm)

Since rough 2003, FDOT has already georectified all the images and lined them up to be seamlessly placed side-by-side. This means the more recent years can be sliced into map tiles quite easiliy. Older images, however, are stored as individual shots with no geographic information embedded in them. I had some success using [MapWarper](https://mapwarper.net/), but it's rather slow work, so I focused on the images that best showed the four main parks. You can [my georectified images](https://mapwarper.net/users/746) there for now, but I may delete those at some point, because MapWarper is a community project using a ton of disk space, so it's not really fair to them to leave those up there.

### Notices of Commencement from the Orange County Comptroller's Office

Even through Disney was basically granted its own municipality in the form of the Reedy Creek Improvement District (RCID), they still had to file paperwork with government of Orange County. In particular, Disney would file a Notice of Commencement when construction began on a project. These notices would contain a brief note of the work being done and also a detailed description of the location for that work. Each document is signed and dated and is also stamped with the date that it was processed by the comptroller's office.

The early years are unfortunately somewhat hit or miss. I don't know whether Disney didn't file everything, or if the comptroller's office doesn't have those records available digitally. There are a lot of holes. But starting in about 1988, with the work to be done on Disney/MGM Studios, records got a lot more frequent and detailed. In the mid-90s, they even started including a printed map with the survey points listed. Those maps are less accurate than I'd like, but they can be good references for names of buildings that aren't otherhwise obvious.

[Comptroller's records search](https://or.occompt.com/recorder/web/)

Many of the scripts in this repository revolve around these documents. There are scripts to download them en masse, scripts to attempt to extract text information from them, and scripts to translate the property descritions into geographic shapes that be imported into GIS tools.

### PLSS survey points from the Orange County Appraiser's Office

The property descriptions from the comptroller's office use the [Public Land Survey System (PLSS)](https://en.wikipedia.org/wiki/Public_Land_Survey_System), which requires a starting point for the property description. That point is referenced in the document, but not given latitude and longitude coordinates. The appraiser's office does have a database of those points. I've included a GeoJSON file in this repositority containing all the points needed for Walt Disney World, but there are also other datasets available from the appraiser's office that might prove useful.

The data is available an ArcGIS service, but it has a weird URL prefix that messes up the scripts I've thrown at it. Rather than try to manually munge the URLs and perhaps introduce more bugs, I found it similar to introduce a redirect service in front of it to simplify things. I've put the [redirector code](https://github.com/gulopine/redirector) in its own repository so that it's easier to deploy it directly to Heroku, for free. You'll need to sign up for a Heroku account, but the app doesn't use any resources that would require a credit card. This button will take you to a simple deployment screen.

[![Deploy](https://www.herokucdn.com/deploy/button.svg)](https://heroku.com/deploy?template=https://github.com/gulopine/redirector&env[INITIAL_REDIRECT]=/arcgis/rest/services/&env[REMOTE_BASE]=https://maps.ocpafl.org/Proxy/proxy.ashx?https://gisapp2.ocpafl.org)

### Building footprints from Microsoft

I ran across this one more recently, so I haven't really looked at it much yet. It might be a convenient way to get building footprints across Walt Disney World without having to trace everything manually.

[US Building Footprints](https://github.com/Microsoft/USBuildingFootprints)

### Variety of information from ArcGIS collections

There are a lot of user-submitted datasets hosted by ArcGIS that cover WDW and the slightly-broader RCID. I haven't looked too much at what's available, and I don't know what the copyright/licensing status is on any of it. Feel free to explore at your own discretion.

[ArcGIS search for "rcid"](https://www.arcgis.com/home/search.html?q=rcid)
[ArcGIS search for "wdw"](https://www.arcgis.com/home/search.html?q=wdw)

### RCID public records

I haven't tried this yet myself, but as an official municipality, RCID is required to make at least some portion of its records public. Like most municipalities, though, data and documents are only available upon request. You'd need to know what you're looking for and how to describe it, as well as being willing to pay for it. The information is technically public, but they're allowed to charge for the administrative overhead of tracking it down as well any physical costs of copying and distributing it (paper copies, CDs, etc).

[RCID public records](https://www.rcid.org/publicrecords/)

### Newspapers.com

This is more about historical information than geographical data. Old newspapers, particularly the [Orlando Sentinel](https://www.newspapers.com/paper/the-orlando-sentinel/4644/), have lots of information about openings and closings, reviews of attractions, event advertisements and other information about the parks over the years. It can also help flesh out histories of the people who owned property prior to Disney.

[Newspapers.com](https://newspapers.com/)

There's a subscription cost in order to retrieve the important newspapers in question, which also makes this a bit of a challenge. But given the volume of information, it's well worth the price, in my opinion. if you do have a subscription, I've included a script in this repository to download newspaper pages programmitically based on search terms.
