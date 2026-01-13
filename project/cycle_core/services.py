from django.utils.timezone import now


from .models import CycleDetails, CycleWindow, CycleStats, MIN_LOG_FOR_STATS
from log_core.models import DailyLog


from datetime import datetime, timedelta, date
import statistics

# authenticated users only
def generate_prediction_based_on_log_count(user, threshold = MIN_LOG_FOR_STATS):
    stats = getattr(user, 'cyclestats', None)
    cycledetails = getattr(user, 'cycledetails', None)
    
    if stats:
        if stats.log_count >= threshold:
            predictions = PredictionBuilder.generateMultiplePredictions(stats, user=user)
        elif stats.log_count < threshold:
            predictions = PredictionBuilder.generateMultiplePredictions(cycledetails, user=user)

        return predictions

    #should never get in this branch, it's a fall-back in case cyclestats were not to exist for some reason
    elif cycledetails:
        return PredictionBuilder.generateMultiplePredictions(cycledetails, user=user)
    
    raise ValueError('CycleStats and CycleDetails not found.')


def update_cycle_stats(cs: CycleStats, min_logs:int=MIN_LOG_FOR_STATS):
        user = cs.user
        if user:
            logs = CycleWindow.objects.filter(user=user, is_prediction=False)
            if cs.log_count < min_logs:
                return
        
            # compute avg cycle duration and menstruation duration from last 6 logs
            # foreach CycleWindow compute
            #   timedelta between menstruation_start and menstruation_end (inclusive)
            #   timedelta between menstruation_start and menstruation_start of next CycleWindow

            recent_windows = list(logs.order_by('-menstruation_start')[:min_logs])  # newest first
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
                men_days = cw.getMenstruationDuration().days
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
            updated = False
            if cycle_lengths:
                new_avg_cycle = int(round(statistics.mean(cycle_lengths)))
                if new_avg_cycle != cs.avg_cycle_duration:
                    cs.avg_cycle_duration = new_avg_cycle
                    updated = True
            if menstruation_lengths:
                new_avg_men = int(round(statistics.mean(menstruation_lengths)))
                if new_avg_men != cs.avg_menstruation_duration:
                    cs.avg_menstruation_duration = new_avg_men
                    updated = True

            if updated:
                cs.save(update_fields=['avg_cycle_duration', 'avg_menstruation_duration'])
            
            # Update ovulation stats based on logged ovulation tests
            update_ovulation_stats(cs)

def calculate_ovulation_timing_from_logs(user, min_logs=MIN_LOG_FOR_STATS):
    """
    Calculate average ovulation timing based on positive ovulation tests in DailyLog.
    Returns a tuple: (avg_ovulation_start_day, avg_ovulation_end_day)
    Returns None if insufficient data.
    """
    logged_cycles = list(
        CycleWindow.objects.filter(
            user=user,
            is_prediction=False
        ).order_by('menstruation_start')  # Chronological order
    )
    
    if len(logged_cycles) < min_logs:
        return None
    
    # Only use cycles where we have boundary data (current + next cycle)
    ovulation_day_offsets = []
    
    for idx, cycle in enumerate(logged_cycles[:-1]):  # Exclude the last cycle
        # Use actual next cycle start as boundary (real cycle length)
        next_cycle_start = logged_cycles[idx + 1].menstruation_start
        
        positive_tests = DailyLog.objects.filter(
            user=user,
            date__gte=cycle.menstruation_start,
            date__lt=next_cycle_start,  # Cycle ends before next menstruation starts
            ovulation_test='POSITIVE'
        ).order_by('date')
        
        if positive_tests.exists():
            first_positive = positive_tests.first()
            day_offset = (first_positive.date - cycle.menstruation_start).days
            ovulation_day_offsets.append(day_offset)
    
    if not ovulation_day_offsets:
        return None
    
    # Calculate average ovulation day (use round() for better precision)
    avg_ovulation_day = statistics.mean(ovulation_day_offsets)
    
    # Define ovulation window as ±2 days from average
    ovulation_start_day = max(0, round(avg_ovulation_day - 2))
    ovulation_end_day = round(avg_ovulation_day + 2)
    
    return (ovulation_start_day, ovulation_end_day)


def update_ovulation_stats(cs: CycleStats):
    # Update CycleStats with calculated ovulation timing based on logged ovulation tests. Falls back to defaults if insufficient data.
    ovulation_timing = calculate_ovulation_timing_from_logs(cs.user)
    
    if ovulation_timing:
        cs.avg_ovulation_start_day = ovulation_timing[0]
        cs.avg_ovulation_end_day = ovulation_timing[1]
        cs.save()
    else:
        # Use defaults if no ovulation test data
        cs.avg_ovulation_start_day = CycleDetails.AVG_MIN_OVULATION_DAY
        cs.avg_ovulation_end_day = CycleDetails.AVG_MAX_OVULATION_DAY
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
    def predictOvulation(first_day_cycle: datetime, ovulation_start_day: int = CycleDetails.AVG_MIN_OVULATION_DAY, ovulation_end_day: int = CycleDetails.AVG_MAX_OVULATION_DAY) -> tuple[datetime, datetime]:
        ovulation_start = first_day_cycle + timedelta(days=ovulation_start_day)
        ovulation_end = first_day_cycle + timedelta(days=ovulation_end_day)

        return(ovulation_start, ovulation_end)

    @staticmethod
    def generateMultiplePredictions(source, times: int = 3, user = None, today = None) -> list:
        prediction_list = []
        
        # Normalize to an initial CycleWindow and avg values
        if isinstance(source, CycleDetails):
            cd = source
            
            latest_real_cw = None
            if user:
                latest_real_cw = CycleWindow.objects.filter(user=user, is_prediction=False).order_by('-menstruation_start').first()
            
            initial_cw = latest_real_cw or cd.asCycleWindow()
            avg_cycle = cd.avg_cycle_duration
            avg_menstruation = cd.avg_menstruation_duration
        
        elif isinstance(source, CycleStats):
            stats = source
            cd = getattr(stats.user, 'cycledetails', None)
            if cd is None:
                raise ValueError('CycleStats provided but related CycleDetails (user.cycledetails) not found.')

            latest_real_cw = CycleWindow.objects.filter(user=stats.user, is_prediction=False).order_by('-menstruation_start').first()
            
            initial_cw = latest_real_cw or cd.asCycleWindow()
            avg_cycle = stats.avg_cycle_duration
            avg_menstruation = stats.avg_menstruation_duration
        else:
            raise TypeError('source must be a CycleDetails or CycleStats instance')

        # Calculate starting point for predictions based on current date
        # If the last period + average cycle length is in the past, jump to next expected period
        if today is None:
            today = now().date()
        
        current_start = initial_cw.menstruation_start
        if isinstance(current_start, datetime):
            current_start = current_start.date()
        
        # Keep advancing until we reach a prediction that starts on or after today
        while current_start + timedelta(days=avg_cycle) < today:
            current_start = current_start + timedelta(days=avg_cycle)
        
        for i in range(times):
            cw = PredictionBuilder.generatePrediction(current_start, avg_cycle, avg_menstruation, user=user)
            prediction_list.append(cw)
            current_start = cw.menstruation_start

        return prediction_list