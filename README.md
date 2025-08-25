# Gmail-Phishing-and-Spam-Filter

# Docker Build and run 

 > docker build -t gmailphishingandspamfilter .

 > docker run -it --name gmailbot --rm --volume $(pwd)/src/:/usr/src/app --net=host gmailphishingandspamfilter:latest

## Initial test
Python script that works together with Gmail API to filter out any phishing/spam emails and report them to Google.