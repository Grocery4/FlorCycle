from .models import CycleDetails, CycleWindow, CycleStats

from datetime import datetime, timedelta, date

#TODO - test this mf
# This should be the 
def generatePredictionBasedOnLogCount(user, threshold = 6):
    stats = user.cyclestats

    # If stats exists   
    if stats:
        if stats.log_count < threshold:
            predictions = PredictionBuilder.generateMultiplePredictions(user.cycledetails)
        elif stats.log_count >= threshold:
            predictions = PredictionBuilder.generateMultiplePredictions(stats)

        return predictions

    # Redundant raise, should not happen
    raise ValueError('CycleStats not found.')



class PredictionBuilder():
    @staticmethod
    def generatePrediction(base_menstruation_date: date, avg_cycle_duration: int, avg_menstruation_duration: int) -> CycleWindow:
        predicted_menstruation_start, predicted_menstruation_end = PredictionBuilder.predictMenstruation(base_menstruation_date, avg_cycle_duration, avg_menstruation_duration)
        min_ovulation_window, max_ovulation_window = PredictionBuilder.predictOvulation(predicted_menstruation_start)

        cwp = CycleWindow(
            menstruation_start=predicted_menstruation_start,
            menstruation_end=predicted_menstruation_end,
            min_ovulation_window=min_ovulation_window,
            max_ovulation_window=max_ovulation_window,
            is_prediction = True
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
    def generateMultiplePredictions(source, times: int = 3) -> list:
        prediction_list = []

        # Normalize to an initial CycleWindow and avg values
        if isinstance(source, CycleDetails):
            cd = source
            initial_cw = cd.asCycleWindow()
            avg_cycle = cd.avg_cycle_duration
            avg_menstruation = cd.avg_menstruation_duration
        
        elif isinstance(source, CycleStats):
            stats = source
            # stats.user should exist; try to get that user's CycleDetails
            cd = getattr(stats.user, 'cycledetails', None)
            if cd is None:
                raise ValueError('CycleStats provided but related CycleDetails (user.cycledetails) not found.')

            # Prefer the most recent CycleWindow for the user (chronological by menstruation_start).
            latest_cw = CycleWindow.objects.filter(user=stats.user).order_by('-menstruation_start').first()
            if latest_cw is not None:
                initial_cw = latest_cw
            else:
                # Fallback to initial CycleWindow generated from CycleDetails
                initial_cw = cd.asCycleWindow()

            avg_cycle = stats.avg_cycle_duration
            avg_menstruation = stats.avg_menstruation_duration
        else:
            raise TypeError('source must be a CycleDetails or CycleStats instance')


        prediction_list.append(initial_cw)

        for i in range(1, times):
            previous_cw = prediction_list[i - 1]
            cw = PredictionBuilder.generatePrediction(previous_cw.menstruation_start, avg_cycle, avg_menstruation)
            prediction_list.append(cw)

        return prediction_list