from .models import CycleDetails, CycleWindowPrediction

from datetime import datetime, timedelta

class PredictionBuilder():
    @staticmethod
    def generatePrediction(cd: CycleDetails) -> CycleWindowPrediction:
        predicted_menstruation_start, predicted_menstruation_end = PredictionBuilder.predictMenstruation(cd)
        min_ovulation_window, max_ovulation_window = PredictionBuilder.predictOvulation(predicted_menstruation_start)

        cwp = CycleWindowPrediction(
            menstruation_start=predicted_menstruation_start,
            menstruation_end=predicted_menstruation_end,
            min_ovulation_window=min_ovulation_window,
            max_ovulation_window=max_ovulation_window
        )

        return cwp

    # TODO - evaluate whether the calculations are accurate according to inspiration website
    @staticmethod
    def predictMenstruation(cd: CycleDetails) -> tuple[datetime, datetime]:
        menstruation_start = cd.last_menstruation_date + timedelta(days=cd.avg_cycle_duration)
        menstruation_end = menstruation_start + timedelta(days=cd.avg_menstruation_duration)

        return(menstruation_start, menstruation_end)

    @staticmethod
    def predictOvulation(first_day_cycle: datetime) -> tuple[datetime, datetime]:
        ovulation_start = first_day_cycle + timedelta(days=CycleDetails.AVG_MIN_OVULATION_DAY)
        ovulation_end = first_day_cycle + timedelta(days=CycleDetails.AVG_MAX_OVULATION_DAY)

        return(ovulation_start, ovulation_end)