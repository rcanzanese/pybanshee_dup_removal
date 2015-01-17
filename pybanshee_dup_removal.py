import sqlite3
import numpy as np
import urlparse
import os

# Where is the database stored?
banshee_db_filename = "/home/raymond/.config/banshee-1/banshee.db"

# Time threshold - songs only considered duplicates if the lengthis are within
# this ms interval
threshold = 5 * 1000

# Banshee uses a sqlite database
conn = sqlite3.connect(banshee_db_filename)
c = conn.cursor()

query = "select CoreTracks.TitleLowered,CoreArtists.NameLowered," +\
    "CoreAlbums.TitleLowered from CoreTracks " +\
    "INNER JOIN CoreArtists on (CoreArtists.ArtistID=CoreTracks.ArtistID) " +\
    "INNER JOIN CoreAlbums on (CoreAlbums.AlbumID=CoreTracks.AlbumID) " +\
    "GROUP BY CoreArtists.NameLowered,CoreAlbums.TitleLowered," +\
    "CoreTracks.TitleLowered HAVING COUNT(*)>1"

c.execute(query)
results = c.fetchall()

print("Processing " + str(len(results)) + " results...")

for r in results:
    title = r[0]
    artist = r[1]
    album = r[2]

    if title is None or artist is None or album is None:
        continue

    if title.find("\"") > 0:
        continue

    # Get the track times and file names
    query = "select CoreTracks.Duration,CoreTracks.Uri,CoreTracks.Rating," +\
        "CoreTracks.TrackNumber,CoreTracks.PlayCount from CoreTracks " +\
        "INNER JOIN CoreArtists on " +\
        "(CoreArtists.ArtistID=CoreTracks.ArtistID) INNER JOIN CoreAlbums " +\
        "on (CoreAlbums.AlbumID=CoreTracks.AlbumID) WHERE " +\
        "CoreTracks.TitleLowered=\"" + title +\
        "\" AND CoreArtists.NameLowered=\"" + artist + "\" AND " +\
        "CoreAlbums.TitleLowered=\"" + album + "\""

    c.execute(query)
    dupes = c.fetchall()
    times = np.zeros(len(dupes))

    for res, i in zip(dupes, range(0, len(dupes))):
        times[i] = res[0]

    idx = np.nonzero(np.abs(times - times[np.random.randint(0, len(times))])
        < threshold)[0]

    scores = np.zeros(idx.shape)

    # Favor the versions with a high rating, track number and play count.
    for i, j in zip(idx, range(0, len(idx))):
        rating = dupes[i][2]
        tracknum = dupes[i][3]
        playcount = dupes[i][4]

        if rating > 0:
            scores[j] += 2
        if tracknum > 0:
            scores[j] += 4
        if playcount > 0:
            scores[j] += 1

    #print("# Keeping "+urlparse.unquote(dupes[idx[-1]][1][7:]));
    # Remove all but the one with the highest score
    idx = np.argsort(scores)
    idx = idx[:-1]
    for i in idx:
        path = urlparse.unquote(dupes[i][1][7:])
        print("Removing " + path)
        try:
            os.remove(path)
        except:
            print("ERROR:  Could not remove.  Probably an encoding " +
                "issue or was already deleted.  Ignoring...")


conn.close()
