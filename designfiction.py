import streamlit as st
import time
import serial
import serial.tools.list_ports
import random


st.set_page_config(page_title="PROSTHETIX LINK", layout="wide")


st.markdown("""
    <style>
    .stApp { background-color: #000000; color: #00FF41; font-family: 'Courier New'; }
    .error { color: #FF0000; font-size: 40px; font-weight: bold; text-shadow: 0 0 10px #FF0000; }
    .success { color: #00FF41; font-size: 40px; font-weight: bold; text-shadow: 0 0 10px #00FF41; }
    .warning { color: #FFD700; font-size: 20px; }
    .metric-card { 
        background: linear-gradient(180deg, #001a00 0%, #000000 100%);
        border: 1px solid #00FF41;
        border-radius: 5px;
        padding: 15px;
        margin: 5px;
    }
    </style>
    """, unsafe_allow_html=True)


@st.cache_resource
def get_serial_connection():
    """Try to establish serial connection (cached to persist across reruns)"""

    ports_to_try = ["COM6", "COM3", "COM4", "COM5", "COM7", "COM8"]
    
    for port in ports_to_try:
        try:
            ser = serial.Serial(port, 115200, timeout=0.1)
            return ser
        except:
            continue
    
    ports = list(serial.tools.list_ports.comports())
    for p in ports:
        keywords = ["CP210", "CH9102", "CH340", "USB", "Serial", "UART", "M5"]
        if any(kw.lower() in p.description.lower() for kw in keywords):
            try:
                ser = serial.Serial(p.device, 115200, timeout=0.1)
                return ser
            except:
                continue
    return None

st.sidebar.title("HARDWARE STATUS")
st.sidebar.write("**Available COM Ports:**")
ports = list(serial.tools.list_ports.comports())
if ports:
    for p in ports:
        st.sidebar.write(f"- `{p.device}`: {p.description}")
else:
    st.sidebar.warning("No COM ports detected!")


if st.sidebar.button("Reconnect Hardware"):
    st.cache_resource.clear()
    st.rerun()


if 'status' not in st.session_state:
    st.session_state.status = "BROKEN"
if 'motor_data' not in st.session_state:
    st.session_state.motor_data = [50] * 50
if 'tension_data' not in st.session_state:
    st.session_state.tension_data = [30] * 50
if 'signal_data' not in st.session_state:
    st.session_state.signal_data = [0] * 50
if 'last_action_time' not in st.session_state:
    st.session_state.last_action_time = None


ser = get_serial_connection()

if ser:
    st.sidebar.success(f"CONNECTED: {ser.name}")
else:
    st.sidebar.error("HARDWARE NOT FOUND")
    st.sidebar.info("**Troubleshooting:**\n- Check USB cable\n- Install CH9102/CP210x driver\n- Check Device Manager for COM port")


st.title("PROSTHETIX-OS // DIAGNOSTIC BRIDGE")


header_ph = st.empty()
body_ph = st.empty()


col1, col2, col3, col4 = st.columns(4)

with col1:
    motor_metric = st.empty()
with col2:
    tension_metric = st.empty()
with col3:
    signal_metric = st.empty()
with col4:
    uptime_metric = st.empty()


st.subheader("REAL-TIME DIAGNOSTICS")
graph_col1, graph_col2 = st.columns(2)

with graph_col1:
    motor_chart = st.empty()
with graph_col2:
    tension_chart = st.empty()

signal_chart = st.empty()


st.subheader("SYSTEM LOG")
log_ph = st.empty()


if st.sidebar.checkbox("Enable Simulation Mode", value=(ser is None)):
    if st.sidebar.button("Simulate Button Press"):
        st.session_state.status = "FIXED"
        st.session_state.last_action_time = time.time()


while True:
    if ser:
        try:
            if ser.in_waiting > 0:
                line = ser.readline().decode('utf-8').strip()
                if "ACTION_RESET_CONFIRMED" in line:
                    st.session_state.status = "FIXED"
                    st.session_state.last_action_time = time.time()
        except Exception as e:
            st.sidebar.warning(f"Read error: {e}")

    is_fixed = st.session_state.status == "FIXED"
    
    if is_fixed:
        new_motor = random.randint(85, 100)
        new_tension = random.randint(45, 55)
        new_signal = random.randint(80, 100)
    else:
        new_motor = random.randint(0, 30)
        new_tension = random.randint(70, 100)  
        new_signal = random.randint(0, 20)
    
    st.session_state.motor_data = st.session_state.motor_data[1:] + [new_motor]
    st.session_state.tension_data = st.session_state.tension_data[1:] + [new_tension]
    st.session_state.signal_data = st.session_state.signal_data[1:] + [new_signal]

    
    motor_metric.metric("MOTOR POWER", f"{new_motor}%", 
                        delta=f"{new_motor - st.session_state.motor_data[-2]}%")
    tension_metric.metric("TENSION", f"{new_tension}%",
                          delta=f"{new_tension - st.session_state.tension_data[-2]}%",
                          delta_color="inverse")
    signal_metric.metric("SIGNAL", f"{new_signal}%",
                         delta=f"{new_signal - st.session_state.signal_data[-2]}%")
    uptime_metric.metric("STATUS", 
                         "ONLINE" if is_fixed else "LOCKED",
                         delta="OK" if is_fixed else "ERROR")

    
    motor_chart.line_chart(st.session_state.motor_data, use_container_width=True)
    tension_chart.line_chart(st.session_state.tension_data, use_container_width=True)
    signal_chart.area_chart(st.session_state.signal_data, use_container_width=True)

    if st.session_state.status == "BROKEN":
        header_ph.markdown('<p class="error"> CRITICAL FAILURE</p>', unsafe_allow_html=True)
        body_ph.markdown("""
        ```
        > CLOUD SYNC.............. [FAIL]
        > MOTOR LOCK.............. [ACTIVE]
        > NEURAL BRIDGE........... [DISCONNECTED]
        > FIRMWARE................ [CORRUPTED]
        
           WAITING FOR MANUAL OVERRIDE...
        ```
        """)
        log_ph.code(f"""
[{time.strftime('%H:%M:%S')}] ERROR: Cloud authentication failed
[{time.strftime('%H:%M:%S')}] WARNING: Motor safety lock engaged
[{time.strftime('%H:%M:%S')}] INFO: Awaiting physical reset signal...
        """)
    else:
        header_ph.markdown('<p class="success"> SYSTEM RESTORED</p>', unsafe_allow_html=True)
        body_ph.markdown("""
        ```
        > MANUAL OVERRIDE......... [RECEIVED]
        > MOTORS.................. [UNLOCKED]
        > TENSION................. [STABLE]
        > NEURAL BRIDGE........... [CONNECTED]
        
         PROSTHETIC FULLY OPERATIONAL
        ```
        """)
        log_ph.code(f"""
[{time.strftime('%H:%M:%S')}] SUCCESS: Manual override accepted
[{time.strftime('%H:%M:%S')}] INFO: Motor lock disengaged
[{time.strftime('%H:%M:%S')}] INFO: All systems nominal
        """)
        
        if st.session_state.last_action_time:
            if time.time() - st.session_state.last_action_time > 5:
                st.session_state.status = "BROKEN"
                st.session_state.last_action_time = None
                st.rerun()

    time.sleep(0.2)