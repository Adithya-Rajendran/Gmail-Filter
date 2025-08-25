# Gmail-Spam-Filter

# Docker Build and run 

 > docker build --no-cache -t gmailfilter .

 > docker run -it --name gmailbot --rm --volume $(pwd)/src:/usr/src/app --volume $(pwd)/model:/usr/src/model --net=host gmailfilter:latest

## Initial test
Python script that works together with Gmail API to filter out any phishing/spam emails and report them to Google.