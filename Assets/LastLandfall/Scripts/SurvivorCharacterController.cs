using System;
using UnityEngine;

namespace LastLandfall.Prototype
{
    /// <summary>
    /// Autonomous survivor/resident character behavior for Last Landfall.
    /// Handles procedural walking motion, idle animation, task assignment, and settlement patrol.
    /// </summary>
    [SelectionBase]
    public sealed class SurvivorCharacterController : MonoBehaviour
    {
        [Header("Identity & Role")]
        [SerializeField] private string residentName = "幸存者";
        [SerializeField] private string profession = "搜救员";
        [SerializeField] private float healthPercent = 100f;
        [SerializeField] private float moralePercent = 85f;

        [Header("Locomotion")]
        [SerializeField] private float walkSpeed = 1.4f;
        [SerializeField] private float wanderRadius = 6.0f;
        [SerializeField] private float idleDurationMin = 3.0f;
        [SerializeField] private float idleDurationMax = 7.0f;

        private Vector3 spawnOrigin;
        private Vector3 currentTarget;
        private bool isWalking;
        private float nextStateTimer;
        private float stepCycle;
        private Transform leftLeg;
        private Transform rightLeg;
        private Transform leftArm;
        private Transform rightArm;
        private Transform head;

        public string ResidentName => residentName;
        public string Profession => profession;
        public float HealthPercent => healthPercent;
        public float MoralePercent => moralePercent;
        public bool IsWalking => isWalking;

        private void Awake()
        {
            spawnOrigin = transform.position;
            currentTarget = spawnOrigin;
            nextStateTimer = UnityEngine.Random.Range(idleDurationMin, idleDurationMax);

            // Locate articulated limbs in model for procedural walk cycle
            leftLeg = transform.Find("Survivor_Worker_Root/UpperLeg_Left");
            rightLeg = transform.Find("Survivor_Worker_Root/UpperLeg_Right");
            leftArm = transform.Find("Survivor_Worker_Root/UpperArm_Left");
            rightArm = transform.Find("Survivor_Worker_Root/UpperArm_Right");
            head = transform.Find("Survivor_Worker_Root/Head");
        }

        private void Update()
        {
            if (isWalking)
            {
                Vector3 toTarget = currentTarget - transform.position;
                toTarget.y = 0f;

                if (toTarget.magnitude > 0.15f)
                {
                    Vector3 moveDir = toTarget.normalized;
                    transform.position += moveDir * (walkSpeed * Time.deltaTime);

                    // Face move direction smoothly
                    Quaternion targetRot = Quaternion.LookRotation(moveDir, Vector3.up);
                    transform.rotation = Quaternion.Slerp(transform.rotation, targetRot, 8f * Time.deltaTime);

                    // Procedural walk animation
                    stepCycle += Time.deltaTime * walkSpeed * 6.0f;
                    float legSwing = Mathf.Sin(stepCycle) * 25f;
                    float armSwing = -Mathf.Sin(stepCycle) * 22f;
                    float verticalBob = Mathf.Abs(Mathf.Sin(stepCycle)) * 0.04f;

                    if (leftLeg != null) leftLeg.localRotation = Quaternion.Euler(legSwing, 0f, 0f);
                    if (rightLeg != null) rightLeg.localRotation = Quaternion.Euler(-legSwing, 0f, 0f);
                    if (leftArm != null) leftArm.localRotation = Quaternion.Euler(armSwing, 0f, 0f);
                    if (rightArm != null) rightArm.localRotation = Quaternion.Euler(-armSwing, 0f, 0f);

                    Vector3 pos = transform.position;
                    // Maintain ground alignment
                    transform.position = new Vector3(pos.x, spawnOrigin.y + verticalBob, pos.z);
                }
                else
                {
                    isWalking = false;
                    nextStateTimer = UnityEngine.Random.Range(idleDurationMin, idleDurationMax);
                    ResetLimbs();
                }
            }
            else
            {
                // Idle breathing & subtle head turn
                nextStateTimer -= Time.deltaTime;
                float breath = Mathf.Sin(Time.time * 2.2f) * 0.015f;
                transform.position = new Vector3(transform.position.x, spawnOrigin.y + breath, transform.position.z);

                if (head != null)
                {
                    float headTurn = Mathf.Sin(Time.time * 0.8f) * 12f;
                    head.localRotation = Quaternion.Euler(0f, headTurn, 0f);
                }

                if (nextStateTimer <= 0f)
                {
                    PickNewDestination();
                }
            }
        }

        private void ResetLimbs()
        {
            if (leftLeg != null) leftLeg.localRotation = Quaternion.identity;
            if (rightLeg != null) rightLeg.localRotation = Quaternion.identity;
            if (leftArm != null) leftArm.localRotation = Quaternion.identity;
            if (rightArm != null) rightArm.localRotation = Quaternion.identity;
        }

        private void PickNewDestination()
        {
            Vector2 randomCircle = UnityEngine.Random.insideUnitCircle * wanderRadius;
            currentTarget = new Vector3(spawnOrigin.x + randomCircle.x, spawnOrigin.y, spawnOrigin.z + randomCircle.y);
            isWalking = true;
        }

        public void SetProfile(string name, string job)
        {
            residentName = name;
            profession = job;
        }

        public void SetSpawnPoint(Vector3 position)
        {
            spawnOrigin = position;
            transform.position = position;
            currentTarget = position;
        }

        /// <summary>
        /// Factory method to spawn a stylized survivor character in the settlement.
        /// </summary>
        public static SurvivorCharacterController Spawn(Vector3 worldPosition, string name, string job, Transform parent = null)
        {
            GameObject prefab = Resources.Load<GameObject>("Models/Characters/Survivor_Worker");
            if (prefab == null)
            {
                Debug.LogWarning("Survivor_Worker model not found in Resources/Models/Characters.");
                return null;
            }

            GameObject residentHost = new GameObject("Survivor | " + name);
            if (parent != null)
            {
                residentHost.transform.SetParent(parent, true);
            }
            residentHost.transform.position = worldPosition;

            GameObject modelInstance = Instantiate(prefab, residentHost.transform, false);
            modelInstance.name = "Survivor_Worker_Root";

            SurvivorCharacterController controller = residentHost.AddComponent<SurvivorCharacterController>();
            controller.SetProfile(name, job);
            controller.SetSpawnPoint(worldPosition);
            return controller;
        }
    }
}
