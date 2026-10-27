using System;
using UnityEngine;

namespace LastLandfall.Prototype
{
    /// <summary>
    /// Dynamic watercraft controller for the Last Landfall rescue speedboat.
    /// Handles wave floating simulation, idle bobbing, engine trim, and manual player piloting.
    /// </summary>
    [SelectionBase]
    public sealed class RescueBoatController : MonoBehaviour
    {
        private static RescueBoatController activeVessel;
        public static RescueBoatController ActiveVessel => activeVessel;

        [Header("Floating Dynamics")]
        [SerializeField] private float waterLevel = -0.92f;
        [SerializeField] private float buoyancyStrength = 1.6f;
        [SerializeField] private float wavePitchAmount = 4.5f;
        [SerializeField] private float waveRollAmount = 7.0f;
        [SerializeField] private float waveBobFrequency = 1.25f;

        [Header("Boat Status")]
        [SerializeField] private string vesselName = "海燕 01 号 (Sea Swallow)";
        [SerializeField] private int crewCapacity = 6;
        [SerializeField] private int currentCrew = 2;
        [SerializeField] private float fuelPercent = 100f;
        [SerializeField] private bool isMoored = true;

        [Header("Piloting Navigation")]
        [SerializeField] private float forwardSpeed = 9.5f;
        [SerializeField] private float reverseSpeed = 3.5f;
        [SerializeField] private float steeringTurnRate = 75f;
        [SerializeField] private bool isPlayerPiloting = false;

        private Vector3 basePosition;
        private Quaternion baseRotation;
        private float wavePhaseOffset;
        private Transform propellerPort;
        private Transform propellerStbd;

        private float currentThrottle;
        private float currentSteer;
        private float currentVelocity;
        private Camera mainCamera;
        private Vector3 originalCameraTarget;
        private float originalCameraSize;

        public string VesselName => vesselName;
        public int CurrentCrew => currentCrew;
        public int CrewCapacity => crewCapacity;
        public float FuelPercent => fuelPercent;
        public bool IsMoored => isMoored;
        public bool IsPlayerPiloting => isPlayerPiloting;

        public event Action<bool> PilotingStateChanged;

        private void Awake()
        {
            activeVessel = this;
            basePosition = transform.position;
            baseRotation = transform.rotation;
            wavePhaseOffset = UnityEngine.Random.Range(0f, Mathf.PI * 2f);

            propellerPort = transform.Find("RescueBoat_Speedboat_Root/Outboard_PropHub_Port");
            propellerStbd = transform.Find("RescueBoat_Speedboat_Root/Outboard_PropHub_Starboard");
            mainCamera = Camera.main;
        }

        private void Update()
        {
            if (isPlayerPiloting)
            {
                HandlePlayerInput();
                UpdateBoatMovement();
            }
            else
            {
                UpdatePassiveWaveBobbing();
            }

            // Keyboard shortcut to toggle boat piloting
            if (Input.GetKeyDown(KeyCode.B))
            {
                TogglePiloting();
            }
        }

        private void HandlePlayerInput()
        {
            float v = Input.GetAxisRaw("Vertical");    // W/S or Up/Down
            float h = Input.GetAxisRaw("Horizontal");  // A/D or Left/Right

            currentThrottle = Mathf.MoveTowards(currentThrottle, v, 3f * Time.deltaTime);
            currentSteer = Mathf.MoveTowards(currentSteer, h, 4f * Time.deltaTime);

            if (Input.GetKeyDown(KeyCode.Escape))
            {
                SetPiloting(false);
            }
        }

        private void UpdateBoatMovement()
        {
            // Steer rotation (bow points -Y in model space, forward in world space)
            if (Mathf.Abs(currentVelocity) > 0.1f || Mathf.Abs(currentThrottle) > 0.05f)
            {
                float turn = currentSteer * steeringTurnRate * Time.deltaTime * Mathf.Sign(currentThrottle != 0 ? currentThrottle : currentVelocity);
                baseRotation = Quaternion.Euler(0f, turn, 0f) * baseRotation;
            }

            // Acceleration & drag
            float targetSpeed = currentThrottle > 0 ? currentThrottle * forwardSpeed : currentThrottle * reverseSpeed;
            currentVelocity = Mathf.MoveTowards(currentVelocity, targetSpeed, 6.5f * Time.deltaTime);

            // Move in boat forward direction (local forward is -Z or transformed forward)
            Vector3 forwardDir = baseRotation * Vector3.forward;
            basePosition += forwardDir * (currentVelocity * Time.deltaTime);

            // Wave listing based on speed
            float speedRatio = Mathf.Abs(currentVelocity) / forwardSpeed;
            float time = Time.time * waveBobFrequency * (1f + speedRatio * 0.8f) + wavePhaseOffset;

            float heave = Mathf.Sin(time) * 0.07f * buoyancyStrength;
            float roll = Mathf.Sin(time * 0.9f) * (waveRollAmount + speedRatio * 4f) - currentSteer * 6f * speedRatio;
            float dynamicPitch = Mathf.Cos(time * 1.2f) * wavePitchAmount - (currentVelocity > 0 ? 3.5f * speedRatio : -1.5f);

            basePosition.y = waterLevel + heave;
            transform.position = basePosition;
            transform.rotation = baseRotation * Quaternion.Euler(dynamicPitch, 0f, roll);

            // Propeller spin
            float propSpin = (currentVelocity * 1200f + 360f) * Time.deltaTime;
            if (propellerPort != null) propellerPort.Rotate(Vector3.forward, propSpin, Space.Self);
            if (propellerStbd != null) propellerStbd.Rotate(Vector3.forward, -propSpin, Space.Self);

            // Consume minor fuel
            if (Mathf.Abs(currentVelocity) > 0.2f)
            {
                fuelPercent = Mathf.Max(0f, fuelPercent - Time.deltaTime * 0.08f);
            }
        }

        private void UpdatePassiveWaveBobbing()
        {
            float time = Time.time * waveBobFrequency + wavePhaseOffset;

            float heave = Mathf.Sin(time) * 0.08f * buoyancyStrength;
            float roll = Mathf.Sin(time * 0.85f) * waveRollAmount;
            float pitch = Mathf.Cos(time * 1.15f) * wavePitchAmount;
            float yawSway = isMoored ? Mathf.Sin(time * 0.4f) * 3.5f : 0f;

            Vector3 currentPos = basePosition;
            currentPos.y = waterLevel + heave;
            transform.position = currentPos;

            Quaternion waveTilt = Quaternion.Euler(pitch, yawSway, roll);
            transform.rotation = baseRotation * waveTilt;
        }

        public void TogglePiloting()
        {
            SetPiloting(!isPlayerPiloting);
        }

        public void SetPiloting(bool piloting)
        {
            if (isPlayerPiloting == piloting) return;
            isPlayerPiloting = piloting;
            isMoored = !piloting;

            var prototype = FindAnyObjectByType<BuildPlacementPrototype>();
            if (prototype != null)
            {
                prototype.SetCameraFollowTarget(piloting ? transform : null);
            }

            PilotingStateChanged?.Invoke(isPlayerPiloting);
        }

        public void SetMoored(bool moored)
        {
            isMoored = moored;
        }

        public void SetBasePosition(Vector3 position, Quaternion rotation)
        {
            basePosition = position;
            baseRotation = rotation;
            transform.SetPositionAndRotation(position, rotation);
        }

        /// <summary>
        /// Factory method to spawn the dynamic rescue speedboat in the scene.
        /// </summary>
        public static RescueBoatController Spawn(Vector3 worldPosition, Quaternion worldRotation, Transform parent = null)
        {
            GameObject prefab = Resources.Load<GameObject>("Models/Vehicles/RescueBoat_Speedboat");
            if (prefab == null)
            {
                Debug.LogWarning("RescueBoat_Speedboat model not found in Resources/Models/Vehicles.");
                return null;
            }

            GameObject boatHost = new GameObject("Rescue Speedboat | Sea Swallow");
            if (parent != null)
            {
                boatHost.transform.SetParent(parent, true);
            }
            boatHost.transform.SetPositionAndRotation(worldPosition, worldRotation);

            GameObject modelInstance = Instantiate(prefab, boatHost.transform, false);
            modelInstance.name = "RescueBoat_Speedboat_Root";

            RescueBoatController controller = boatHost.AddComponent<RescueBoatController>();
            controller.SetBasePosition(worldPosition, worldRotation);
            return controller;
        }
    }
}
