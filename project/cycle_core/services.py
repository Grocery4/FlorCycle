from .models import CycleDetails, CycleWindow

from datetime import datetime, timedelta

class PredictionBuilder():
    @staticmethod
    def generatePrediction(cd: CycleDetails) -> CycleWindow:
        predicted_menstruation_start, predicted_menstruation_end = PredictionBuilder.predictMenstruation(cd.last_menstruation_date, cd.avg_cycle_duration, cd.avg_menstruation_duration)
        min_ovulation_window, max_ovulation_window = PredictionBuilder.predictOvulation(predicted_menstruation_start)

        cwp = CycleWindow(
            menstruation_start=predicted_menstruation_start,
            menstruation_end=predicted_menstruation_end,
            min_ovulation_window=min_ovulation_window,
            max_ovulation_window=max_ovulation_window
        )
        return cwp

    @staticmethod
    def predictMenstruation(last_menstruation_date: datetime.date, avg_cycle_duration: int, avg_menstruation_duration: int) -> tuple[datetime, datetime]:
        menstruation_start = last_menstruation_date + timedelta(days=avg_cycle_duration)
        menstruation_end = menstruation_start + timedelta(days=avg_menstruation_duration - 1)

        return(menstruation_start, menstruation_end)

    @staticmethod
    def predictOvulation(first_day_cycle: datetime) -> tuple[datetime, datetime]:
        ovulation_start = first_day_cycle + timedelta(days=CycleDetails.AVG_MIN_OVULATION_DAY)
        ovulation_end = first_day_cycle + timedelta(days=CycleDetails.AVG_MAX_OVULATION_DAY)

        return(ovulation_start, ovulation_end)

    @staticmethod
    def generateMultiplePredictions(cd: CycleDetails, times: int) -> list:
        prediction_list = []

        prediction_list.append(cd.asCycleWindow())
        for i in range(1,times):
            previous_cw = prediction_list[i-1]

            predicted_menstruation_start, predicted_menstruation_end = PredictionBuilder.predictMenstruation(previous_cw.menstruation_start, cd.avg_cycle_duration, cd.avg_menstruation_duration)            
            predicted_ovulation_start, predicted_ovulation_end = PredictionBuilder.predictOvulation(predicted_menstruation_start)

            cw = CycleWindow(
                menstruation_start=predicted_menstruation_start,
                menstruation_end=predicted_menstruation_end,
                min_ovulation_window=predicted_ovulation_start,
                max_ovulation_window=predicted_ovulation_end
            )

            prediction_list.append(cw)

        return prediction_list