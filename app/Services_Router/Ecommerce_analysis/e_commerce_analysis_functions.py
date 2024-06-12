import nltk
nltk.download('vader_lexicon')


from nltk.sentiment.vader import SentimentIntensityAnalyzer

analyzer = SentimentIntensityAnalyzer()

def reviewSentiment(text):
    text = text.lower()

    sentiment = analyzer.polarity_scores(text)

    return sentiment['compound']


def reviewAnalysis(reviews):
    if len(reviews) == 0:
        return {
            "sentiment": "Neutral",
            "pos_per": 0,
            "neg_per": 0,
            "neu_per": 0
        }
    pos = 0
    neg = 0
    neu = 0
    for review in reviews:
        if review["review_sentiment"] >= 0.05:
            pos += 1
        elif review["review_sentiment"] <= -0.05:
            neg += 1
        else:
            neu += 1

    #find which is the maximum between pos,neg and neu
    threshold = max(pos,neg,neu)

    if pos == neg:
        sentiment = "Neutral"
    elif pos >= threshold:
        sentiment = "Positive"
    elif neg >= threshold:
        sentiment = "Negative"
    else:
        sentiment = "Neutral"

    pos_per = pos/len(reviews)*100
    neg_per = neg/len(reviews)*100
    neu_per = neu/len(reviews)*100

    #create an obejct to return sentiment and percentages
    analysis = {
        "sentiment": sentiment,
        "pos_per": pos_per,
        "neg_per": neg_per,
        "neu_per": neu_per
    }

    return analysis


#apply profanity analysis to the reviews and return the result along with the reviews
