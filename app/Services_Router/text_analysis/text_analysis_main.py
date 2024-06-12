from fastapi import  UploadFile, HTTPException,APIRouter
from .. text_analysis.sentiment_analysis import sentAnalysis
from .. text_analysis.profanity_analysis import profanityAnalysis
import io
import pandas as pd

router = APIRouter(
    prefix= "/Text-Analysis",
    tags=['Text-Analysis']
)

@router.post("/positivity-analyze")
async def sentiment_analysis(data: dict):
    try:
        text = data['text']
    except KeyError as e:
        raise HTTPException(status_code=400, detail="An exception occurred. Error: " + str(e))

    try:
        result = sentAnalysis(text)
    except Exception as e:
        raise HTTPException(status_code=500, detail="An exception occurred. Error: " + str(e))

    return result

@router.post("/profanity-analyze")
async def profanity_analysis(file_text: UploadFile):
    try:
        data_bank = {}
        if file_text:
            file_contents = await file_text.read()
            decoded_file = file_contents.decode('utf-8')
            reader = pd.read_csv(io.StringIO(decoded_file))
            for _, row in reader.iterrows():
                data_bank[row['id']] = row['clean_text']
            data = {"status": "success"}
        else:
            data = {"status": "failed"}

    except Exception as e:
        raise HTTPException(status_code=400, detail="An exception occurred. Error: " + str(e))

    try:
        result = profanityAnalysis(data_bank)
    except Exception as e:
        raise HTTPException(status_code=500, detail="An exception occurred. Error: " + str(e))

    return result

