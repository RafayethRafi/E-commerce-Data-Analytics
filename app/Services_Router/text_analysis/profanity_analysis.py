from profanity_check import predict, predict_prob
import numpy as np
def profanityAnalysis(data_bank):
    
    result = []
    for id, rev_dict in data_bank.items():
        temp = {}
        text_full = rev_dict['review']
        # Split the test intu multiple line for line wise analysis.
        text = text_full.split('.')
        words = text_full.split(' ')
        # Remove the last item in the list if it is empty
        if(text[-1] == ''):
            text.pop()
        predict_text=predict(text)
        predict_prob_text=predict_prob(text)
        predict_prob_text[0]=round(predict_prob_text[0], 2)
        if predict_prob_text[0] >  .05:
            predict_words= predict(words)
            indices_predict_words = np.where(predict_words == 1)[0]
            profanity_words = []
            for i in indices_predict_words:
                profanity_words.append(words[i])
            temp ={
                "product_id" : rev_dict['product_id'],
                "product_name" : rev_dict['product_name'],
                "review_id" : id,
                "text" : text[0],
                "profanity_text" : predict_prob_text[0]*100,
                "profanity_words" : profanity_words
            }
            result.append(temp)

    return result

