import time
import board
import busio
from adafruit_pca9685 import PCA9685

# ---------------- I2C + PCA9685 SETUP ----------------
i2c = busio.I2C(board.SCL, board.SDA)
pca = PCA9685(i2c, address=0x40)
pca.frequency = 50

# ---------------- SERVO CHANNELS ----------------
# Left Leg
P1_BELOW = 0
P1_ABOVE = 1

# Right Leg
P2_BELOW = 7
P2_ABOVE = 6

# Pelvis
P3_LEFT = 9
P3_RIGHT = 8

# ---------------- GLOBAL STATE ----------------
current_angles = {
    P1_BELOW: 135.0,
    P1_ABOVE: 135.0,
    P2_BELOW: 135.0,
    P2_ABOVE: 135.0,
    P3_LEFT: 135.0,
    P3_RIGHT: 135.0,
}

# ---------------- LOW-LEVEL COMMAND ----------------
def set_us(channel, us):
    period_us = 1_000_000 / pca.frequency
    ticks_12bit = int(round(us * 4096 / period_us))
    ticks_12bit = max(0, min(4095, ticks_12bit))
    duty_16bit = int(round(ticks_12bit * 65535 / 4095))
    pca.channels[channel].duty_cycle = duty_16bit


def deg_to_us(degrees):
    """Map 0-270 degrees to 500-2500us (generic)."""
    degrees = max(0, min(270, degrees))
    us = 500 + (degrees / 270.0) * 2000
    return int(us)


# ---------------- MOVE ONE PAIR ----------------
def move_pair(ch_below, ch_above, end_below, end_above, duration_sec):
    global current_angles

    start_below = current_angles[ch_below]
    start_above = current_angles[ch_above]

    start_us_below = deg_to_us(start_below)
    end_us_below = deg_to_us(end_below)

    start_us_above = deg_to_us(start_above)
    end_us_above = deg_to_us(end_above)

    step_delay = 0.02
    total_steps = max(1, int(duration_sec / step_delay))

    step_below = (end_us_below - start_us_below) / total_steps
    step_above = (end_us_above - start_us_above) / total_steps

    for i in range(total_steps + 1):
        set_us(ch_below, int(start_us_below + i * step_below))
        set_us(ch_above, int(start_us_above + i * step_above))
        time.sleep(step_delay)

    current_angles[ch_below] = end_below
    current_angles[ch_above] = end_above

# --- Option B: Move ALL Pairs Simultaneously ---
def move_all_pairs(end_p1_b, end_p1_a, end_p2_b, end_p2_a, end_p3_b, end_p3_a, duration_sec):
    """Calculates the math for all 6 servos and moves them at the exact same time."""
    global current_angles

    # Grab all 6 start positions
    s_p1_b = deg_to_us(current_angles[P1_BELOW])
    s_p1_a = deg_to_us(current_angles[P1_ABOVE])
    s_p2_b = deg_to_us(current_angles[P2_BELOW])
    s_p2_a = deg_to_us(current_angles[P2_ABOVE])
    s_p3_b = deg_to_us(current_angles[P3_LEFT])
    s_p3_a = deg_to_us(current_angles[P3_RIGHT])

    # Convert all 6 end positions
    e_p1_b = deg_to_us(end_p1_b)
    e_p1_a = deg_to_us(end_p1_a)
    e_p2_b = deg_to_us(end_p2_b)
    e_p2_a = deg_to_us(end_p2_a)
    e_p3_b = deg_to_us(end_p3_b)
    e_p3_a = deg_to_us(end_p3_a)

    step_delay = 0.02
    total_steps = max(1, int(duration_sec / step_delay))

    # Calculate steps for all 6 servos
    step_p1_b = (e_p1_b - s_p1_b) / total_steps
    step_p1_a = (e_p1_a - s_p1_a) / total_steps
    step_p2_b = (e_p2_b - s_p2_b) / total_steps
    step_p2_a = (e_p2_a - s_p2_a) / total_steps
    step_p3_b = (e_p3_b - s_p3_b) / total_steps
    step_p3_a = (e_p3_a - s_p3_a) / total_steps

    for i in range(total_steps + 1):
        set_us(P1_BELOW, int(s_p1_b + (i * step_p1_b)))
        set_us(P1_ABOVE, int(s_p1_a + (i * step_p1_a)))

        set_us(P2_BELOW, int(s_p2_b + (i * step_p2_b)))
        set_us(P2_ABOVE, int(s_p2_a + (i * step_p2_a)))

        set_us(P3_LEFT, int(s_p3_b + (i * step_p3_b)))
        set_us(P3_RIGHT, int(s_p3_a + (i * step_p3_a)))

        time.sleep(step_delay) # One single pause applies to all 6 servos!

    # Update all 6 trackers at the end
    current_angles[P1_BELOW] = end_p1_b
    current_angles[P1_ABOVE] = end_p1_a
    current_angles[P2_BELOW] = end_p2_b
    current_angles[P2_ABOVE] = end_p2_a
    current_angles[P3_LEFT] = end_p3_b
    current_angles[P3_RIGHT] = end_p3_a

def squat():
    try:
        for cycle in range(2):
            print(f"\n--- Cycle {cycle + 1} of 4 ---")
#first loop
            move_all_pairs(
                end_p1_b = 50,
                end_p1_a = 220,
                end_p2_b = 220,
                end_p2_a = 50,
                end_p3_b = 135,
                end_p3_a = 135,
                duration_sec = 1.5)
            time.sleep(1)
            move_all_pairs(
                end_p1_b = 135,
                end_p1_a = 135,
                end_p2_b = 135,
                end_p2_a = 135,
                end_p3_b = 135,
                end_p3_a = 135,
                duration_sec = 1.5)
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nTest interrupted.")

    finally:
        print("Cleaning up board...")
        pca.deinit()
        print("Done.")


# ---------------- EXECUTION ----------------
if __name__ == "__main__":
   squat() 
