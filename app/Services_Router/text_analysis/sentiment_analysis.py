from nltk.sentiment.vader import SentimentIntensityAnalyzer

# nltk.download('vader_lexicon')
analyzer = SentimentIntensityAnalyzer()

def sentAnalysis(text):

    #convert to lowercase
    text = text.lower()
            
    # Split the test intu multiple line for line wise analysis.
    text = text.split('.')
    # Remove the last item in the list if it is empty
    if(text[-1] == ''):
        text.pop()
    
    result = {}
    pos = 0
    neg = 0
    neu = 0

    avg_sentiment = 0
    # Perform sentiment analysis on each line
    for line in text:
        sentiment = analyzer.polarity_scores(line)
        if sentiment['compound'] >= 0.05:
            res = 'Positive'
            pos += sentiment['compound']
        elif sentiment['compound'] <= - 0.05:
            res = 'Negative'
            neg += sentiment['compound']
        else:
            res = 'Neutral'
            neu += sentiment['compound']

            
        
        # Store the line and res in a dictionary result
        result[line] = res

    total_sentiment = pos + neg + neu

    threshold = 0.5
    
    if pos > threshold:
        sentiment = 'Positive'
    elif neg > threshold:
        sentiment = 'Negative'
    elif neu > threshold:
        sentiment = 'Neutral'

    # Return the analysis result in a dictionary
    result = {"overall_sentiment": sentiment,
            "detailed_analysis" : result
            }
    return result