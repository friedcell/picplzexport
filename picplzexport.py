import sys, os, urllib, urllib2, json, time, getpass

try:
	from bs4 import BeautifulSoup
	def get_attr(tag, attr):
		return tag.attrs[attr]
except:
	try:
		from BeautifulSoup import BeautifulSoup
		def get_attr(tag, attr):
			for t in tag.attrs:
				if t[0] == attr:
					return t[1]
			return None
	except:
		print """You don't have BeautifulSoup installed.

You can do that with one of the following commands:
easy_install beautifulsoup4
pip install beautifulsoup4
apt-get install python-beautifulsoup4

You can also install BeautifulSoup 3.

More info at http://www.crummy.com/software/BeautifulSoup/"""
		sys.exit()

root = "http://picplz.com"
referer = None
baseheaders = {
	"Accept": "text/html",
	"User-Agent": "Mozilla/5.0 (PicPlz Downloader)"
}
photos = []

cookieprocessor = urllib2.HTTPCookieProcessor()
opener = urllib2.build_opener(cookieprocessor)
urllib2.install_opener(opener)

def make_request(url, data=None, headers=None):
	h = {}
	h.update(baseheaders)
	h.update(headers or {})
	req = urllib2.Request("%s%s" % (root, url), urllib.urlencode(data) if data else None, h)
	global referer
	if referer:
		req.add_unredirected_header("Referer", referer)
	res = urllib2.urlopen(req)
	referer = res.geturl()
	return res

def get_photos(username, password):
	print "Getting CSRF token..."
	res = make_request("/login/?next=/yourphotos/")
	csrf = ""
	for c in res.headers.getheaders("set-cookie"):
		if c.find("csrftoken=") == 0:
			csrf = c.split(";")[0].split("=")[1]
	print "Logging in & fetching first photos..."
	res = make_request("/login/?next=/yourphotos/", {"email": username, "password": password, "csrfmiddlewaretoken": csrf})
	html = res.read()
	last_id = html.split("\"last_id\":")[1].split("}")[0]
	extract_photos(html)
	if last_id:
		get_more_photos(last_id)
	download_photos()

def get_more_photos(last_id):
	print "Fetching more photos (%s)" % last_id 
	data = {
		"_": int(time.time()),
		"last_id": last_id,
		"predicate": "yourphotos",
		"view_type": ""
		}
	res = make_request("/api/v1/picfeed_get?%s" % urllib.urlencode(data), None, {
		"Accept": "application/json, */*",
		"X-Requested-With": "XMLHttpRequest",
		})
	obj = json.loads(res.read())
	if obj.get("value"):
		v = obj.get("value")
		extract_photos(v.get("html"))
		if v.get("has_next"):
			get_more_photos(v.get("last_id"))

def extract_photos(html):
	global photos
	soup = BeautifulSoup(html)
	for d in soup("div", attrs={"class": "pic line"}):
		url = get_attr(d.find("a", attrs={"class": "download"}), "href")
		p = {
			"title": "",
			"id": url.split("/")[-3],
			"url": url,
			"filename": photo_name(url)
		}
		title = d.find("div", attrs={"class": "caption line"})
		if title:
			p["title"] = title.text
		photos.append(p)

def photo_name(url):
	return "picplz_%s.jpg" % url.split("/")[-3]

def download_photos():
	global photos
	print "%d photos extracted" % len(photos)
	e = 0
	n = 0
	for p in photos:
		filename = p["filename"]
		if not os.path.exists(filename):
			download_file(p["url"], p["filename"])
			n += 1
		else:
			e += 1
	print "%d photo(s) downloaded, %d already existed." % (n, e)

def download_file(url, filename):
	u = urllib2.urlopen(url)
	f = open(filename, 'wb')
	meta = u.info()
	file_size = int(meta.getheaders("Content-Length")[0])
	print "Downloading: %s Bytes: %s" % (filename, file_size)
	file_size_dl = 0
	block_sz = 8192
	while True:
		buffer = u.read(block_sz)
		if not buffer:
			break
		file_size_dl += len(buffer)
		f.write(buffer)
		status = r"%10d  [%3.2f%%]" % (file_size_dl, file_size_dl * 100. / file_size)
		status = status + chr(8)*(len(status)+1)
		print status,
	f.close()

def build_html(username):
	global phtoos
	imagelist = []
	for p in photos:
		imagelist.append('<li id="i%(id)s"><h2>%(title)s</h2><img src="%(filename)s" /></li>' % p)
	h = """<!doctype html>
<html>
	<head>
		<meta charset="utf-8" />
		<title>picplz backup for %(username)s</title>
	</head>
	<body>
		<h1>picplz backup for %(username)s</h1>
		<ol>
			%(images)s
		</ol>
	</body>
</html>""" % {"username": username, "images": "\n\t\t\t".join(imagelist)}
	username = re.sub('[-\s]+', '-', re.sub('[^\w\s-]', '', username.split("@")[0]).strip().lower())
	filename = "picplz_%s_backup.html" % username
	f = open(filename, 'w')
	f.write(h)
	f.close()
	print "HTML built:", filename

if __name__ == "__main__":
	if len(sys.argv) < 2:
		print "Usage: python picplzexport.py [username]"
	else:
		username = sys.argv[1]
		password = getpass.getpass("Password: ")
		get_photos(username, password)
		build_html(username)

