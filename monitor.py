import time
import snapshot
# initialize CSV files once before the loop starts
snapshot.init_csv()
snapshot.init_anomaly_csv()

# last_state tracks what condition each metric was in during the previous cycle
# starts as OK because we assume everything is fine until proven otherwise
last_state = {
    'cpu' : 'OK',
    'ram' : 'OK',
    'disk': 'OK'
}
print("=== System Watcher Started — Press Ctrl+C to stop ===\n")
try:
    while True:
        # pass last_state in, get updated state back
        last_state = snapshot.run_snapshot(last_state)

        # wait 5 seconds before next cycle
        time.sleep(5)

except KeyboardInterrupt:
    print("\n=== System Watcher Stopped ===")