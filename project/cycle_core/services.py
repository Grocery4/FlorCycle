from django.conf import settings

from .models import CycleDetails, CycleWindow, CycleStats, MIN_LOG_FOR_STATS
from datetime import datetime, timedelta, date
import statistics

#TODO - test this mf
def generatePredictionBasedOnLogCount(user, threshold = MIN_LOG_FOR_STATS):
    stats = user.cyclestats
    cycledetails = user.cycledetails
    
    if stats:
        if stats.log_count >= threshold:
            predictions = PredictionBuilder.generateMultiplePredictions(stats, user=user)
        elif stats.log_count < threshold:
            predictions = PredictionBuilder.generateMultiplePredictions(cycledetails, user=user)

        return predictions

    elif cycledetails:
        return PredictionBuilder.generateMultiplePredictions(cycledetails)
    
    raise ValueError('CycleStats and CycleDetails not found.')


def updateCycleStats(cs: CycleStats):
        user = cs.user
        if user:
            logs = CycleWindow.objects.filter(user=user, is_prediction=False)
        
            if logs.count() <= MIN_LOG_FOR_STATS:
                return
        
            # compute avg cycle duration and menstruation duration from last 6 logs
            # foreach CycleWindow compute
            #   timedelta between menstruation_start and menstruation_end (inclusive)
            #   timedelta between menstruation_start and menstruation_start of next CycleWindow

            recent_windows = list(logs.order_by('-menstruation_start')[:MIN_LOG_FOR_STATS])  # newest first
            if not recent_windows:
                return

            # work in chronological order (oldest -> newest)
            recent_windows.reverse()

            menstruation_lengths = []
            cycle_lengths = []

            for idx, cw in enumerate(recent_windows):
                start = cw.menstruation_start
                end = cw.menstruation_end

                # normalize possible datetime -> date (subtraction works for both)
                if isinstance(start, datetime):
                    start = start.date()
                if isinstance(end, datetime):
                    end = end.date()

                # menstruation duration: inclusive days (end - start + 1)
                men_days = (end - start).days + 1
                if men_days > 0:
                    menstruation_lengths.append(men_days)

                # cycle length: days between this start and next start
                if idx < len(recent_windows) - 1:
                    next_start = recent_windows[idx + 1].menstruation_start
                    if isinstance(next_start, datetime):
                        next_start = next_start.date()
                    cycle_days = (next_start - start).days
                    if cycle_days > 0:
                        cycle_lengths.append(cycle_days)

            # update cyclestats values (round to nearest int)
            if cycle_lengths:
                cs.avg_cycle_duration = int(round(statistics.mean(cycle_lengths)))
            if menstruation_lengths:
                cs.avg_menstruation_duration = int(round(statistics.mean(menstruation_lengths)))

            cs.save()

class PredictionBuilder():
    @staticmethod
    def generatePrediction(base_menstruation_date: date, avg_cycle_duration: int, avg_menstruation_duration: int, user = None) -> CycleWindow:
        predicted_menstruation_start, predicted_menstruation_end = PredictionBuilder.predictMenstruation(base_menstruation_date, avg_cycle_duration, avg_menstruation_duration)
        min_ovulation_window, max_ovulation_window = PredictionBuilder.predictOvulation(predicted_menstruation_start)

        cwp = CycleWindow(
            user=user,
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
    def generateMultiplePredictions(source, times: int = 3, user = None) -> list:
        prediction_list = []

        # Normalize to an initial CycleWindow and avg values
        if isinstance(source, CycleDetails):
            cd = source
            
            last_real_cw = None
            if user:
                last_real_cw = CycleWindow.objects.filter(user=user, is_prediction=False).order_by('-menstruation_start').first()
            
            initial_cw = last_real_cw or cd.asCycleWindow()

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


        current_start = initial_cw.menstruation_start
        for i in range(times):
            cw = PredictionBuilder.generatePrediction(current_start, avg_cycle, avg_menstruation, user=user)
            prediction_list.append(cw)
            current_start = cw.menstruation_start

        return prediction_list