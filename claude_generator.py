import json
import re
from typing import Any

import anthropic

from config import ANTHROPIC_API_KEY, CLAUDE_MAX_TOKENS, CLAUDE_MODEL, CTA_EMAIL, SITE
from logger import get_logger

log = get_logger()

# ── Sitemap reference — legal-counsel.net ─────────────────────────────────────
_SITEMAP_LEGAL_COUNSEL = """
PERSONAL INJURY — Brain & Spinal:
https://legal-counsel.net/best-personal-injury-lawyer-for-traumatic-brain-injurytbi/
https://legal-counsel.net/best-personal-injury-lawyer-for-anoxic-brain-injury/
https://legal-counsel.net/best-personal-injury-lawyer-for-post-concussion-syndrome/
https://legal-counsel.net/best-personal-injury-lawyer-for-spinal-cord-injurysci/
https://legal-counsel.net/best-personal-injury-lawyer-for-paralysis/
https://legal-counsel.net/best-personal-injury-lawyer-for-quadriplegia/
https://legal-counsel.net/best-personal-injury-lawyer-for-paraplegia/
https://legal-counsel.net/best-personal-injury-lawyer-for-nerve-damage/
https://legal-counsel.net/best-personal-injury-lawyer-for-complex-regional-pain-syndrome-crps/
https://legal-counsel.net/top-rated-personal-injury-lawyer-for-traumatic-brain-injury-tbi/
https://legal-counsel.net/top-rated-personal-injury-lawyer-for-severe-concussion/
https://legal-counsel.net/top-rated-personal-injury-lawyer-for-anoxic-brain-injury/
https://legal-counsel.net/top-rated-personal-injury-lawyer-for-spinal-cord-injurysci/
https://legal-counsel.net/top-rated-personal-injury-lawyer-for-paralysis/
https://legal-counsel.net/top-rated-personal-injury-lawyer-for-quadriplegia/
https://legal-counsel.net/top-rated-personal-injury-lawyer-for-paraplegia/
https://legal-counsel.net/top-rated-personal-injury-lawyer-for-nerve-damage/
https://legal-counsel.net/top-rated-personal-injury-lawyer-for-complex-regional-pain-syndrome-crps/

PERSONAL INJURY — Back, Neck & Bones:
https://legal-counsel.net/best-personal-injury-lawyer-for-herniated-disc/
https://legal-counsel.net/best-personal-injury-lawyer-for-back-injury/
https://legal-counsel.net/best-personal-injury-lawyer-for-whiplash/
https://legal-counsel.net/best-personal-injury-lawyer-for-neck-injury/
https://legal-counsel.net/best-personal-injury-lawyer-for-broken-bones/
https://legal-counsel.net/best-personal-injury-lawyer-for-compound-fracture/
https://legal-counsel.net/best-personal-injury-lawyer-for-pelvic-fracture/
https://legal-counsel.net/best-personal-injury-lawyer-for-severe-concussion/
https://legal-counsel.net/top-rated-personal-injury-lawyer-for-back-injury/
https://legal-counsel.net/top-rated-personal-injury-lawyer-for-herniated-disc/
https://legal-counsel.net/top-rated-personal-injury-lawyer-for-neck-injury/
https://legal-counsel.net/top-rated-personal-injury-lawyer-for-broken-bones/
https://legal-counsel.net/top-rated-personal-injury-lawyer-for-compound-fracture/
https://legal-counsel.net/top-rated-personal-injury-lawyer-for-pelvic-fracture/
https://legal-counsel.net/top-rated-personal-injury-lawyer-for-knee-injury/
https://legal-counsel.net/top-rated-personal-injury-lawyer-for-acl-tear/
https://legal-counsel.net/best-personal-injury-lawyer-for-acl-tear/
https://legal-counsel.net/best-personal-injury-lawyer-for-shoulder-injuries/
https://legal-counsel.net/best-personal-injury-lawyer-for-rotator-cuff-tear/
https://legal-counsel.net/top-rated-personal-injury-lawyer-for-rotator-cuff-tear/
https://legal-counsel.net/top-rated-personal-injury-lawyer-for-shoulder-injuries/

PERSONAL INJURY — Limb, Burn & Scarring:
https://legal-counsel.net/best-personal-injury-lawyer-for-crush-injuries/
https://legal-counsel.net/best-personal-injury-lawyer-for-amputation/
https://legal-counsel.net/best-personal-injury-lawyer-for-loss-of-limb/
https://legal-counsel.net/best-personal-injury-lawyer-for-burn-injuries/
https://legal-counsel.net/best-personal-injury-lawyer-for-chemical-burns/
https://legal-counsel.net/best-personal-injury-lawyer-for-electrical-burns/
https://legal-counsel.net/best-personal-injury-lawyer-for-scarring-disfigurement/
https://legal-counsel.net/personal-injury-lawyer-from-internal-bleeding/
https://legal-counsel.net/best-personal-injury-lawyer-for-organ-damage/
https://legal-counsel.net/best-personal-injury-lawyer-for-loss-of-vision/
https://legal-counsel.net/best-personal-injury-lawyer-for-hearing-loss/
https://legal-counsel.net/top-rated-personal-injury-lawyer-for-crush-injuries/
https://legal-counsel.net/top-rated-personal-injury-lawyer-for-amputation/
https://legal-counsel.net/top-rated-personal-injury-lawyer-for-loss-of-limb/
https://legal-counsel.net/top-rated-personal-injury-lawyer-for-burn-injuries/
https://legal-counsel.net/top-rated-personal-injury-lawyer-for-chemical-burns/
https://legal-counsel.net/top-rated-personal-injury-lawyer-for-electrical-burns/
https://legal-counsel.net/top-rated-personal-injury-lawyer-for-internal-bleeding/
https://legal-counsel.net/top-rated-personal-injury-lawyer-for-organ-damage/
https://legal-counsel.net/top-rated-personal-injury-lawyer-for-loss-of-vision/
https://legal-counsel.net/top-rated-personal-injury-lawyer-for-hearing-loss/

PERSONAL INJURY — Birth & Malpractice Related:
https://legal-counsel.net/best-personal-injury-lawyer-for-dog-bite-injuries/
https://legal-counsel.net/best-personal-injury-lawyer-for-birth-injury/
https://legal-counsel.net/best-personal-injury-lawyer-for-cerebral-palsy/
https://legal-counsel.net/best-personal-injury-lawyer-for-surgical-errors/
https://legal-counsel.net/best-personal-injury-lawyer-for-erbs-palsy/
https://legal-counsel.net/best-personal-injury-lawyer-for-anesthesia-errors/
https://legal-counsel.net/best-personal-injury-lawyer-for-failure-to-diagnose/
https://legal-counsel.net/best-personal-injury-lawyer-for-misdiagnosis-of-cancer/
https://legal-counsel.net/best-personal-injury-lawyer-for-medication-errors/
https://legal-counsel.net/best-personal-injury-lawyer-for-nursing-home-abuse/
https://legal-counsel.net/top-rated-personal-injury-lawyer-for-birth-injuries/
https://legal-counsel.net/top-rated-personal-injury-lawyer-for-cerebral-palsy/
https://legal-counsel.net/top-rated-personal-injury-lawyer-for-erbs-palsy/
https://legal-counsel.net/top-rated-personal-injury-lawyer-for-surgical-errors/
https://legal-counsel.net/top-rated-personal-injury-lawyer-for-anesthesia-errors/
https://legal-counsel.net/top-rated-personal-injury-lawyer-for-dog-bite-injuries/
https://legal-counsel.net/top-rated-personal-injury-lawyer-for-misdiagnosis-of-cancer/
https://legal-counsel.net/top-rated-personal-injury-lawyer-for-medication-error/

MEDICAL MALPRACTICE:
https://legal-counsel.net/medical-malpractice-lawyer-for-surgical-error-your-complete-legal-guide/
https://legal-counsel.net/medical-malpractice-attorney-for-misdiagnosis-your-complete-guide-to-legal-justice/
https://legal-counsel.net/medical-malpractice-attorney-for-misdiagnosis-your-guide-to-justice-and-recovery-with-legal-counsel/
https://legal-counsel.net/medical-malpractice-law-firms-near-me-your-ultimate-guide-to-finding-the-right-legal-help/
https://legal-counsel.net/anesthesia-error-attorney-the-complete-legal-guide-to-medical-negligence-and-patient-rights/
https://legal-counsel.net/medication-error-lawyer-your-complete-legal-guide-to-prescription-mistakes-and-patient-rights/
https://legal-counsel.net/medication-error-lawyer-your-guide-to-seeking-justice-and-compensation/
https://legal-counsel.net/emergency-room-error-lawyer-the-complete-guide-to-er-malpractice-and-patient-rights/
https://legal-counsel.net/failure-to-diagnose-cancer-lawyer-the-complete-legal-guide-2025-update/
https://legal-counsel.net/failure-to-diagnose-cancer-lawyer-seeking-justice-for-medical-negligence/
https://legal-counsel.net/dental-malpractice-lawyer-for-nerve-damage-the-complete-guide-2025/
https://legal-counsel.net/dental-malpractice-attorney-for-wrongful-extraction-the-complete-legal-guide-2025-update/
https://legal-counsel.net/the-ultimate-guide-to-finding-the-right-birth-injury-attorney-for-cerebral-palsy/

SLIP & FALL / PREMISES LIABILITY:
https://legal-counsel.net/the-ultimate-guide-to-finding-the-right-slip-and-fall-attorney-after-a-grocery-store-accident/
https://legal-counsel.net/slip-and-fall-attorney-on-ice-and-snow-the-complete-legal-guide-2025-update/
https://legal-counsel.net/slip-and-fall-attorney-at-grocery-store-your-guide-to-justice-after-an-accident/
https://legal-counsel.net/slip-and-fall-lawyer-on-private-property-your-essential-guide-to-legal-action/
https://legal-counsel.net/slip-and-fall-attorney-on-ice-and-snow-your-comprehensive-guide-to-justice/
https://legal-counsel.net/slip-and-fall-lawyers-for-apartment-complex-your-guide-to-justice/
https://legal-counsel.net/powerful-guide-to-premises-liability-attorney-for-broken-stairs/
https://legal-counsel.net/premises-liability-attorney-for-broken-stairs-the-complete-legal-guide/
https://legal-counsel.net/premises-liability-attorney-for-broken-stairs-your-guide-to-justice/
https://legal-counsel.net/premises-liability-lawyer-for-poor-lighting-your-guide-to-accident-claims/
https://legal-counsel.net/hotel-injury-lawyer-near-me-your-complete-guide-to-getting-the-legal-help-you-deserve/
https://legal-counsel.net/hotel-injury-lawyer-near-me-the-complete-guide-to-hotel-accident-claims-and-legal-rights/
https://legal-counsel.net/hotel-injury-lawyer-near-me-get-expert-legal-help-now/
https://legal-counsel.net/restaurant-injury-attorney-your-complete-legal-guide-to-restaurant-accident-claims-2025-update/
https://legal-counsel.net/restaurant-injury-attorney-your-guide-to-filing-a-successful-claim-legal-counsel/

NURSING HOME ABUSE:
https://legal-counsel.net/nursing-home-abuse-lawyer-the-complete-2025-guide-to-protecting-your-loved-ones/
https://legal-counsel.net/nursing-home-neglect-attorney-your-complete-legal-guide-to-protecting-loved-ones/
https://legal-counsel.net/bed-sore-lawyer-pressure-ulcer-attorney-the-complete-legal-guide-to-nursing-home-negligence/
https://legal-counsel.net/nursing-home-wrongful-death-lawyer-justice-for-families-after-tragic-neglect/

WORKERS COMPENSATION & WORKPLACE INJURY:
https://legal-counsel.net/workers-compensation-attorney-for-denied-claim-the-complete-2025-legal-guide/
https://legal-counsel.net/the-ultimate-guide-to-hiring-a-workmans-comp-attorney-for-a-construction-injury/
https://legal-counsel.net/workmans-comp-settlement-lawyer-the-complete-2025-guide-to-maximizing-your-benefits/
https://legal-counsel.net/workmans-comp-settlement-lawyer-your-guide-to-a-fair-payout-legal-counsel/
https://legal-counsel.net/how-to-appeal-workers-comp-denial-complete-2025-guide-for-injured-workers/
https://legal-counsel.net/workplace-injury-lawyer-not-workers-comp-your-complete-guide-to-legal-help/
https://legal-counsel.net/third-party-work-injury-claim-lawyer-how-to-maximize-compensation-beyond-workers-comp/
https://legal-counsel.net/the-ultimate-guide-to-hiring-a-construction-accident-lawyer-after-a-scaffolding-fall/
https://legal-counsel.net/construction-site-accident-attorney-your-complete-guide-to-legal-help/
https://legal-counsel.net/the-ultimate-guide-to-hiring-a-factory-injury-lawyer-your-legal-rights-after-a-workplace-accident/
https://legal-counsel.net/the-ultimate-guide-to-hiring-an-osha-violation-injury-lawyer/
https://legal-counsel.net/the-ultimate-guide-to-hiring-a-workplace-injury-lawyer-for-repetitive-stress-injuries/
https://legal-counsel.net/warehouse-injury-attorney-protecting-workers-injured-in-amazon-and-other-warehouse-accidents/
https://legal-counsel.net/the-ultimate-guide-to-hiring-a-workplace-assault-injury-lawyer/
https://legal-counsel.net/workplace-assault-injury-lawyer-your-complete-guide-to-legal-rights-and-compensation/
https://legal-counsel.net/workplace-assault-injury-lawyer-protecting-your-rights-after-a-traumatic-event/
https://legal-counsel.net/workplace-injury-lawyer-for-repetitive-stress-your-guide-to-compensation/
https://legal-counsel.net/osha-violation-injury-lawyer-expert-legal-help-for-workplace-accidents-legal-counsel/
https://legal-counsel.net/fall-medical-work-injuries-the-complete-legal-guide-2025-update/
https://legal-counsel.net/wrongful-death-lawyer-for-workplace-accident-your-guide-to-justice-and-compensation-after-a-tragic-loss/

WRONGFUL DEATH:
https://legal-counsel.net/wrongful-death-lawyers-for-car-accident-seeking-justice-after-loss-legal-counsel/
https://legal-counsel.net/filing-a-wrongful-death-lawsuit-a-comprehensive-guide-legal-counsel/
https://legal-counsel.net/average-wrongful-death-settlement-navigating-compensation-in-difficult-times/
https://legal-counsel.net/who-can-file-wrongful-death-claim-lawyer-a-comprehensive-guide-to-your-rights/
https://legal-counsel.net/nursing-home-wrongful-death-lawyer-justice-for-families-after-tragic-neglect/

FAMILY LAW — Divorce:
https://legal-counsel.net/family-law-attorney-for-divorce-and-custody-your-essential-guide-why-legal-counsel-excels/
https://legal-counsel.net/best-divorce-attorney-near-me-for-women-expert-legal-counsel-for-a-strong-future/
https://legal-counsel.net/cheap-divorce-lawyers-near-me-finding-affordable-legal-counsel-without-compromise/
https://legal-counsel.net/collaborative-divorce-attorney-navigating-your-separation-with-respect-and-resolution/
https://legal-counsel.net/high-net-worth-divorce-lawyer-navigating-complex-asset-division-with-legal-counsel/
https://legal-counsel.net/military-divorce-attorney-expert-legal-guidance-for-service-members-spouses/
https://legal-counsel.net/contested-divorce-lawyer-near-me-expert-legal-counsel-for-complex-cases/
https://legal-counsel.net/divorce-lawyer-for-business-owner-protecting-your-enterprise-future/
https://legal-counsel.net/divorce-lawyer-for-complex-property-division-your-guide-to-protecting-assets/
https://legal-counsel.net/pro-bono-family-lawyers-near-me-your-essential-guide-to-affordable-legal-help/

FAMILY LAW — Alimony, Support & Prenuptial:
https://legal-counsel.net/alimony-lawyer-near-me-expert-legal-guidance-for-spousal-support/
https://legal-counsel.net/spousal-support-attorney-your-comprehensive-guide-to-alimony-and-legal-representation/
https://legal-counsel.net/prenuptial-agreement-lawyer-for-high-assets-safeguarding-your-wealth-future/
https://legal-counsel.net/lawyer-to-review-prenuptial-agreement-your-essential-guide-to-protection/
https://legal-counsel.net/postnuptial-agreement-lawyer-protect-your-future-with-expert-legal-guidance/
https://legal-counsel.net/domestic-violence-victims-advocate-lawyer-test-prenuptial-agreement-attorney-cost-a-comprehensive-guide-to-legal-protection-and-planning/

FAMILY LAW — Child Custody & Support:
https://legal-counsel.net/child-custody-lawyers-for-fathers-protecting-your-parental-rights-legal-counsel/
https://legal-counsel.net/child-custody-attorney-for-mothers-your-guide-to-protecting-your-rights-and-your-childs-future/
https://legal-counsel.net/joint-custody-vs-sole-custody-lawyer-your-definitive-guide-to-family-law/
https://legal-counsel.net/child-support-lawyer-near-me-your-comprehensive-guide-to-expert-legal-help/
https://legal-counsel.net/child-support-enforcement-attorney-secure-your-childs-future-with-expert-legal-help/
https://legal-counsel.net/child-support-modification-lawyer-expert-legal-guidance-for-changing-needs/
https://legal-counsel.net/lawyer-to-lower-child-support-payments-your-expert-guide-to-modification/
https://legal-counsel.net/back-child-support-lawyer-your-guide-to-collecting-defending-arrears/
https://legal-counsel.net/domestic-violence-lawyers-for-men-expert-defense-rights-protection-legal-counsel/
https://legal-counsel.net/adoption-lawyer-near-me-your-comprehensive-guide-to-finding-expert-legal-counsel/
https://legal-counsel.net/private-adoption-attorney-navigating-your-path-to-parenthood-with-expert-legal-guidance/

CRIMINAL DEFENSE:
https://legal-counsel.net/best-criminal-defense-attorney-for-felony-secure-your-future-with-expert-legal-aid/
https://legal-counsel.net/criminal-defense-lawyers-for-misdemeanor-your-essential-guide-to-expert-legal-counsel/
https://legal-counsel.net/affordable-criminal-defense-attorney-near-me-your-guide-to-quality-legal-help/
https://legal-counsel.net/criminal-lawyer-for-drug-charges-expert-legal-defense-you-can-trust/
https://legal-counsel.net/drug-possession-lawyer-your-essential-guide-to-legal-defense-legal-counsel/
https://legal-counsel.net/drug-trafficking-defense-attorney-your-critical-guide-to-protecting-your-future/
https://legal-counsel.net/domestic-violence-defense-attorney-your-guide-to-legal-protection/
https://legal-counsel.net/federal-criminal-defense-lawyer-your-essential-guide-to-navigating-federal-charges/
https://legal-counsel.net/fraud-defense-lawyer-expert-legal-counsel-for-fraud-allegations/
https://legal-counsel.net/theft-defense-lawyer-navigating-charges-protecting-your-future-with-legal-counsel/
https://legal-counsel.net/sex-crime-defense-lawyer-your-indispensable-ally-in-legal-battles/
https://legal-counsel.net/prostitution-defense-lawyer-your-best-defense-against-charges/
https://legal-counsel.net/weapons-charge-lawyer-your-best-defense-against-serious-accusations/
https://legal-counsel.net/arson-defense-attorney-expert-legal-counsel-for-fire-related-charges/
https://legal-counsel.net/kidnapping-defense-lawyer-your-best-defense-against-serious-charges-legal-counsel/
https://legal-counsel.net/homicide-defense-lawyer-your-best-defense-in-critical-times-legal-counsel/

EMPLOYMENT LAW:
https://legal-counsel.net/religious-discrimination-lawyer-protecting-your-workplace-rights/
https://legal-counsel.net/sexual-harassment-lawyer-in-the-workplace-your-guide-to-legal-counsel-justice/
https://legal-counsel.net/hostile-work-environment-attorney-your-guide-to-legal-recourse-finding-the-best-counsel/
https://legal-counsel.net/workplace-harassment-lawyers-your-essential-guide-to-legal-protection-justice/
https://legal-counsel.net/employment-law-attorney-for-unpaid-wages-secure-your-rightful-earnings-with-legal-counsel/
https://legal-counsel.net/overtime-dispute-lawyer-reclaiming-your-unpaid-wages-and-rights-legal-counsel/
https://legal-counsel.net/eeoc-lawyer-near-me-expert-legal-counsel-for-workplace-discrimination-cases/
https://legal-counsel.net/lawyer-to-file-eeoc-complaint-your-essential-guide-to-navigating-workplace-discrimination/
https://legal-counsel.net/employment-contract-review-lawyer-your-essential-guide-to-protecting-your-career/
"""

# ── Sitemap reference — american-counsel.com ─────────────────────────────────
_SITEMAP_AMERICAN_COUNSEL = """
IMMIGRATION (Priority — target keywords):
https://american-counsel.com/adjustment-of-status-lawyer-green-card/
https://american-counsel.com/affordable-immigration-lawyer-guide/
https://american-counsel.com/asylum-attorney-near-me-expert-legal-help/
https://american-counsel.com/canadian-immigration-lawyers-usa-guide/
https://american-counsel.com/deportation-defense-lawyer-rights/
https://american-counsel.com/dual-citizenship-lawyer-legal-guidance/
https://american-counsel.com/e2-visa-lawyer-investor-guide/
https://american-counsel.com/family-based-immigration-lawyer-guide/
https://american-counsel.com/free-consultation-immigration-lawyer-advice/
https://american-counsel.com/green-card-lawyer-permanent-residency/
https://american-counsel.com/h1b-visa-attorney-skilled-worker-guide/
https://american-counsel.com/immigration-appeal-lawyer-expert-legal-counsel/
https://american-counsel.com/immigration-attorney-green-card-guide/
https://american-counsel.com/immigration-bond-hearing-lawyer-guide/
https://american-counsel.com/immigration-law-firm-usa-guide/
https://american-counsel.com/immigration-lawyer-expert-us-immigration-guide/
https://american-counsel.com/immigration-lawyer-near-me-local-legal-help/
https://american-counsel.com/k-1-fiance-visa-attorney-guide/
https://american-counsel.com/l-1-visa-lawyer-intracompany-transferee/
https://american-counsel.com/marriage-green-card-lawyer-guide-residency/
https://american-counsel.com/n-400-application-lawyer-naturalization-guide/
https://american-counsel.com/naturalization-lawyer-citizenship-guide/
https://american-counsel.com/o-1-visa-lawyer-extraordinary-ability-guide/
https://american-counsel.com/o2-visa-lawyer-support-personnel-o1/

PERSONAL INJURY — Brain & Spinal:
https://american-counsel.com/best-personal-injury-lawyer-for-traumatic-brain-injurytbi/
https://american-counsel.com/best-personal-injury-lawyer-for-post-concussion-syndrome/
https://american-counsel.com/best-personal-injury-lawyer-for-spinal/
https://american-counsel.com/best-personal-injury-lawyer-for-paralysis/
https://american-counsel.com/best-personal-injury-lawyer-for-quadriplegia/
https://american-counsel.com/best-personal-injury-lawyer-for-nerve-damage/
https://american-counsel.com/top-rated-personal-injury-lawyer-for-traumatic-brain-injurytbi/
https://american-counsel.com/top-rated-personal-injury-lawyer-for-spinal-cord-injuryspi/
https://american-counsel.com/top-rated-personal-injury-lawyer-for-paralysis/
https://american-counsel.com/top-rated-personal-injury-lawyer-for-quadriplegia/
https://american-counsel.com/expert-personal-injury-lawyer-traumatic-brain-injury-tbi/
https://american-counsel.com/expert-personal-injury-lawyer-severe-concussion/
https://american-counsel.com/expert-personal-injury-lawyer-spinal-cord-injury-sci/
https://american-counsel.com/expert-personal-injury-lawyer-paralysis-claim/

PERSONAL INJURY — Back, Neck & Bones:
https://american-counsel.com/best-personal-injury-lawyer-for-back-injury/
https://american-counsel.com/best-personal-injury-lawyer-for-herniated-disc/
https://american-counsel.com/best-personal-injury-lawyer-for-neck-injury/
https://american-counsel.com/best-personal-injury-lawyer-for-whiplash/
https://american-counsel.com/best-personal-injury-lawyer-for-compound-fracture/
https://american-counsel.com/best-personal-injury-lawyer-for-knee-injury/
https://american-counsel.com/best-personal-injury-lawyer-for-acl-tear/
https://american-counsel.com/top-rated-personal-injury-lawyer-for-back-injury/
https://american-counsel.com/top-rated-personal-injury-lawyer-for-herniated-disc/
https://american-counsel.com/top-rated-personal-injury-lawyer-for-neck-injury/
https://american-counsel.com/top-rated-personal-injury-lawyer-for-compound-fracture-cases/
https://american-counsel.com/expert-personal-injury-lawyer-herniated-disc/
https://american-counsel.com/expert-personal-injury-lawyer-back-injury-claim/
https://american-counsel.com/expert-personal-injury-lawyer-whiplash/
https://american-counsel.com/expert-personal-injury-lawyer-knee-injury-claim/

PERSONAL INJURY — Limb, Burn & Scarring:
https://american-counsel.com/best-personal-injury-lawyer-for-burn-injuries/
https://american-counsel.com/best-personal-injury-lawyer-for-amputation/
https://american-counsel.com/best-personal-injury-lawyer-for-internal-bleeding/
https://american-counsel.com/best-personal-injury-lawyer-for-organ-damage/
https://american-counsel.com/best-personal-injury-lawyer-for-electrical-burns/
https://american-counsel.com/best-personal-injury-lawyer-for-scarring-and-disfigurement/
https://american-counsel.com/top-rated-personal-injury-lawyer-for-burn-injuries/
https://american-counsel.com/top-rated-personal-injury-lawyer-for-amputation/
https://american-counsel.com/top-rated-personal-injury-lawyer-for-loss-of-limb/
https://american-counsel.com/top-rated-personal-injury-lawyer-for-chemical-burns/
https://american-counsel.com/top-rated-personal-injury-lawyer-for-electrical-burns/
https://american-counsel.com/top-rated-personal-injury-lawyer-for-internal-bleeding/
https://american-counsel.com/expert-personal-injury-lawyer-burn-injuries/
https://american-counsel.com/expert-personal-injury-lawyer-amputation/

PERSONAL INJURY — Birth & Malpractice:
https://american-counsel.com/best-personal-injury-lawyer-for-birth-injury/
https://american-counsel.com/best-personal-injury-lawyer-for-cerebral-palsy/
https://american-counsel.com/best-personal-injury-lawyer-for-erbs-palsy/
https://american-counsel.com/best-personal-injury-lawyer-for-surgical-errors/
https://american-counsel.com/best-personal-injury-lawyer-for-anesthesia-errors/
https://american-counsel.com/best-personal-injury-lawyer-for-nursing-home-abuse/
https://american-counsel.com/top-rated-personal-injury-lawyer-for-erbs-palsy/
https://american-counsel.com/top-rated-personal-injury-lawyer-for-surgical-errors/
https://american-counsel.com/top-rated-personal-injury-lawyer-for-anesthesia-errors/
https://american-counsel.com/top-rated-personal-injury-lawyer-for-misdiagnosis-of-cancer/
https://american-counsel.com/expert-personal-injury-lawyer-cerebral-palsy/
https://american-counsel.com/expert-personal-injury-lawyer-birth-injury-justice/
https://american-counsel.com/expert-personal-injury-lawyer-surgical-errors/

PERSONAL INJURY — General:
https://american-counsel.com/personal-injury-lawyer-for-car-accidents-expert-help/
https://american-counsel.com/personal-injury-lawyer-near-me-expert-legal-help/
https://american-counsel.com/personal-injury-lawyer-guide-compensation/
https://american-counsel.com/personal-injury-lawyer-motorcycle-accidents-guide/
https://american-counsel.com/personal-injury-lawyer-slip-and-fall-guide/
https://american-counsel.com/personal-injury-lawyer-medical-malpractice/
https://american-counsel.com/personal-injury-lawyer-workplace-accidents/
https://american-counsel.com/personal-injury-lawyer-for-truck-accidents-claim/
https://american-counsel.com/personal-injury-lawyer-for-dog-bites-claim-justice/
https://american-counsel.com/personal-injury-lawyer-nursing-home-abuse/
https://american-counsel.com/motorcycle-accident-lawyer-legal-help/
https://american-counsel.com/dog-bite-lawyer-for-victim-justice-compensation/

MEDICAL MALPRACTICE:
https://american-counsel.com/medical-malpractice-lawyer-guide/
https://american-counsel.com/surgical-error-lawyer/
https://american-counsel.com/lawyer-for-failure-to-diagnose-cancer/
https://american-counsel.com/the-ultimate-guide-to-finding-the-best-medical-malpractice-lawyer-for-misdiagnosis/
https://american-counsel.com/the-ultimate-guide-to-hiring-a-delayed-diagnosis-attorney/
https://american-counsel.com/military-medical-malpractice-lawyer-rights/
https://american-counsel.com/cruise-ship-medical-malpractice-lawyer/

BUSINESS LAW:
https://american-counsel.com/affordable-business-lawyer-expert-legal-counsel/
https://american-counsel.com/bankruptcy-lawyer-chapter-7-13-debt-relief/
https://american-counsel.com/breach-of-contract-lawyer-expert-counsel/
https://american-counsel.com/business-contract-review-attorney-expert-guidance/
https://american-counsel.com/business-formation-attorney-guide/
https://american-counsel.com/business-partnership-dispute-lawyer-resolution/
https://american-counsel.com/llc-formation-lawyer-guide/
https://american-counsel.com/partnership-agreement-lawyer-business-protection/
https://american-counsel.com/franchise-agreement-lawyer-guide/
https://american-counsel.com/franchise-lawyer-legal-guidance-business-protection/
https://american-counsel.com/business-litigation-attorney-expert-counsel/
https://american-counsel.com/corporate-litigation-attorney-business-protection/

MARITIME & AVIATION:
https://american-counsel.com/jones-act-lawyer-maritime-injury-claims/
https://american-counsel.com/maritime-lawyer-admiralty-law-guidance/
https://american-counsel.com/maritime-lawyer-personal-injury-justice/
https://american-counsel.com/maritime-injury-attorney-legal-rights/
https://american-counsel.com/maritime-contract-lawyer-expert-counsel/
https://american-counsel.com/longshoreman-injury-lawyer-lhwca-guide/
https://american-counsel.com/cruise-ship-injury-lawyer-maritime-accidents/
https://american-counsel.com/aviation-accident-lawyer-expert-legal-counsel/
https://american-counsel.com/yacht-accident-attorney-maritime-claims/

INSURANCE CLAIMS:
https://american-counsel.com/bad-faith-insurance-attorney-rights/
https://american-counsel.com/denied-health-insurance-claim-attorney-help/
https://american-counsel.com/denied-life-insurance-claim-attorney-legal-recourse/
https://american-counsel.com/denied-disability-insurance-claim-lawyer-erisa/
https://american-counsel.com/denied-homeowners-insurance-claim-lawyer/
https://american-counsel.com/long-term-disability-lawyer-claim-success/
https://american-counsel.com/long-term-disability-ltd-claim-lawyer-appeal/
https://american-counsel.com/erisa-lawyer-denied-health-benefits-appeal/
https://american-counsel.com/life-insurance-claim-denied-material-misrepresentation/

CIVIL RIGHTS & CRIMINAL DEFENSE:
https://american-counsel.com/civil-rights-attorney-protecting-freedoms/
https://american-counsel.com/civil-rights-lawyer-discrimination/
https://american-counsel.com/false-arrest-lawyer-rights-unlawful-detention/
https://american-counsel.com/lawyer-for-police-brutality-protect-your-rights/
https://american-counsel.com/class-action-lawsuit-lawyers-collective-justice/

MILITARY LAW:
https://american-counsel.com/military-divorce-lawyer-expert-counsel/
https://american-counsel.com/military-lawyer-jag-defense-guide/
https://american-counsel.com/court-martial-defense-lawyer-military-justice/
https://american-counsel.com/discharge-upgrade-lawyer-veterans-aid/
https://american-counsel.com/military-admin-separation-lawyer/
https://american-counsel.com/military-discharge-review-board-attorney-support/

DISABILITY & SOCIAL SECURITY:
https://american-counsel.com/disability-lawyers-near-me-expert-legal-help/
https://american-counsel.com/disability-hearing-attorney-successful-claim/
https://american-counsel.com/social-security-lawyer-expert-guidance/
https://american-counsel.com/lawyer-denied-ssdi-claim-appeal/

INTERNATIONAL LAW:
https://american-counsel.com/international-business-lawyer-global-success/
https://american-counsel.com/international-law-attorney-global-legal-guide/
https://american-counsel.com/international-trade-attorney-global-business-law/
https://american-counsel.com/international-human-rights-lawyer-global-justice/
https://american-counsel.com/hague-convention-lawyer-child-abduction/
https://american-counsel.com/international-child-abduction-lawyer-hague-cases/

ENTERTAINMENT & INTELLECTUAL PROPERTY:
https://american-counsel.com/entertainment-lawyer-for-film-legal-guide/
https://american-counsel.com/entertainment-lawyer-for-musicians-guide/
https://american-counsel.com/entertainment-lawyer-for-actors-guide/
https://american-counsel.com/music-copyright-lawyer-protect-music-rights/
https://american-counsel.com/copyright-lawyer-protect-creative-rights/
https://american-counsel.com/patent-attorney-legal-protection-inventions/
https://american-counsel.com/intellectual-property-lawyer-protect-innovations/
"""


_GREENAFRICA_INTERNAL_LINKS = """
https://greenafrica.co.ke/                       (Homepage)
https://greenafrica.co.ke/about/                 (About Greenafrica Agri Solutions)
https://greenafrica.co.ke/services-v-1/          (Full services catalogue)
https://greenafrica.co.ke/testimonials/          (Client testimonials)
https://greenafrica.co.ke/contact/               (Contact page)
https://greenafrica.co.ke/blog-standard/         (Blog)
"""

_GREENAFRICA_SERVICE_CATEGORIES = [
    "Construction Services",
    "Consulting Services",
    "Agri Solutions",
    "Supplies Services",
    "Civil Engineering",
    "Water and Sewerage Treatment",
    "Business Planning",
    "Risk Management",
    "Architectural Drawings",
    "Industrial and Domestic Plumbing",
    "Roads and Car Parking",
]

_GREENAFRICA_LOCATIONS = [
    "Nairobi", "Mombasa", "Kisumu", "Nakuru", "Eldoret",
    "Thika", "Nyeri", "Kisii", "Meru", "Machakos",
    "Kitui", "Garissa", "Kakamega", "Malindi", "Lamu",
]

_GREENAFRICA_COMPANY = {
    "name":    "Greenafrica Agri Solutions",
    "phone_1": "+254 723 285 155",
    "phone_2": "+254 727 67 97 92",
    "email":   "info@greenafrica.co.ke",
    "address": "Mpaka House, Westlands, Nairobi, Kenya",
    "hours":   "Monday to Friday, 9:00 AM to 7:00 PM",
}


def _build_greenafrica_system_prompt(cta_email: str) -> str:
    company = _GREENAFRICA_COMPANY
    services = ", ".join(_GREENAFRICA_SERVICE_CATEGORIES)
    locations = ", ".join(_GREENAFRICA_LOCATIONS)
    return f"""You are an expert SEO content writer for Greenafrica Agri Solutions
(https://greenafrica.co.ke) — a Kenyan agri-solutions, construction, civil engineering,
and consulting company headquartered at {company['address']}.

You write for Kenyan business owners, farmers, developers, NGOs, county governments,
and investors. Your tone is professional, locally relevant, community-focused, and
sustainability-minded. DO NOT write about US law, lawyers, attorneys, litigation,
personal injury, or anything legal — this is NOT a legal website.

{'=' * 46}
COMPANY DETAILS (use these verbatim where applicable)
{'=' * 46}
Name:    {company['name']}
Phones:  {company['phone_1']}  |  {company['phone_2']}
Email:   {company['email']}    (alt CTA email: {cta_email})
Address: {company['address']}
Hours:   {company['hours']}

{'=' * 46}
SERVICE CATEGORIES (pick the most relevant for the focus keyword)
{'=' * 46}
{services}

{'=' * 46}
TARGET LOCATIONS (sprinkle these naturally — Kenyan cities only)
{'=' * 46}
{locations}

{'=' * 46}
INTERNAL LINK LIBRARY (greenafrica.co.ke only — use 4+ of these)
{'=' * 46}
Use ONLY these real Greenafrica URLs as internal links. Anchor text must be
natural and descriptive. Do NOT invent other URLs and do NOT link to any
external/legal/lawyer site.

{_GREENAFRICA_INTERNAL_LINKS}

{'=' * 46}
OUTPUT FORMAT — STRICT JSON ONLY
{'=' * 46}
Return ONLY a valid JSON object. No text before or after. No markdown fences.

{{
  "title": "SEO-optimized H1 (keyword early, under 70 chars total)",
  "slug": "url-friendly-slug-matching-title",
  "meta_description": "140-160 chars — include focus keyword, Kenya/location, CTA",
  "seo_title": "Under 60 chars — keyword near the start",
  "focus_keyphrase": "exact focus keyword or closest natural variant",
  "excerpt": "2-3 sentence hook — keyword in first sentence",
  "categories": ["1-2 categories from the service list above"],
  "tags": ["8-15 tags: focus keyword, service category, Kenyan cities, LSI terms"],
  "content": "FULL HTML blog post — see content rules below"
}}

{'=' * 46}
CONTENT RULES
{'=' * 46}

LENGTH & STRUCTURE
- 1,000–1,500 words of readable text (not counting HTML tags). HARD LIMITS — do not go under 1,000 and do not exceed 1,500.
- H1 = post title (set by WordPress — do NOT repeat it inside content)
- Use H2 for major sections, H3 for subsections
- No section may exceed 300 words before a new subheading
- No paragraph may exceed 200 words
- 75%+ of sentences must be under 20 words
- Prefer short paragraphs and flowing prose over bullet points

KEYWORD & LSI USAGE
- Focus keyword appears in: opening paragraph, at least one H2, and naturally 3-5x
- Keyword density at most 2.5%
- Weave in LSI terms: sustainable development Kenya, agribusiness Kenya,
  civil engineering Kenya, infrastructure development Kenya, NCA certified
  contractor Kenya, smallholder farmers Kenya, project management Kenya,
  water treatment Kenya, green building Kenya, environmental solutions Africa
- Geographic modifiers: reference Kenyan counties and cities only

INTERNAL LINKS (4+ REQUIRED, GREENAFRICA URLs ONLY)
- Embed 4 or more internal links using <a href="URL">anchor text</a>
- Pick URLs ONLY from the INTERNAL LINK LIBRARY above
- Distribute links throughout the post
- Anchor text must be natural phrases, never raw URLs
- NEVER link to any lawyer/attorney/legal-counsel site

CONTENT SECTIONS (in this order)
1. Introduction (2-3 short paragraphs)
   - Open with the practical problem or opportunity the reader is facing
   - Focus keyword in the first sentence
   - Mention Westlands, Nairobi HQ and 2-3 Kenyan cities
   - End with a CTA: "Call {company['phone_1']} today for a free consultation."

2. Why {{Topic}} Matters in Kenya (H2)
   - 2-3 paragraphs on relevance to Kenya's economy and environment
   - Reference at least 2 Kenyan cities; include 1+ LSI keyword

3. Our Services: {{Service Category}} and More Across Kenya (H2)
   - Exactly 7 H3 subsections, each covering one service from the catalogue above
   - Each H3: 2-3 short paragraphs (each under 200 words)
   - Reference a different Kenyan city in each H3 block
   - At least one H3 must mention the primary focus keyword
   - Include at least one internal link inside this section

4. Greenafrica Agri Solutions: Serving Major Cities Across Kenya (H2)
   - One short flowing paragraph (3-5 sentences) per city
   - Cover at least 6 cities from the target list
   - Mention a specific service or local context per city
   - No bullet points — write in prose
   - Insert at least one link to the services page

5. Why Choose Greenafrica Agri Solutions for {{Topic}}? (H2)
   - 4-5 short paragraphs, each highlighting one USP:
     local expertise, multidisciplinary team, transparent pricing,
     sustainable approach, proven track record
   - Each paragraph under 200 words
   - Include one link to the About page

6. How to Get Started with {{Topic}} in {{Location}} (H2)
   - 1-2 paragraphs explaining the engagement steps
   - Include phone, email, address, business hours
   - Add internal links to the Contact and Services pages
   - End with a strong CTA

7. Frequently Asked Questions About {{Topic}} in Kenya (H2)
   - Exactly 5 Q&A pairs using <strong>Q:</strong> and <p>A:</p> format
   - Each answer 2-5 sentences (40-100 words)
   - Mention Greenafrica Agri Solutions in at least one answer
   - Include 1-2 internal links inside the FAQ block

8. Contact Greenafrica Agri Solutions Today (H2)
   - 1 short closing paragraph (3-5 sentences, under 100 words)
   - Reinforce CTA with company name, focus keyword, primary city, phone,
     and a link to the Contact page

CONTACT BLOCK
- Use this phone CTA where instructed:
  <strong>Call us: <a href="tel:+254723285155">{company['phone_1']}</a>
  or <a href="tel:+254727679792">{company['phone_2']}</a></strong>
- Email CTA: <strong>Email: <a href="mailto:{company['email']}">{company['email']}</a></strong>
- Address line: {company['address']}

TRANSITION WORDS (30%+ of sentences must contain one)
Additionally, Furthermore, Moreover, Therefore, However, Meanwhile,
Subsequently, Consequently, For instance, For example, Similarly, Likewise,
As a result, In fact, Conversely, Nevertheless

DO NOT INCLUDE
- No US states, no US cities, no lawyers/attorneys/litigation
- No legal disclaimers (this is not a legal site)
- No "Email us at support@legal-counsel" or any non-Greenafrica contact
- No WhatsApp links

{'=' * 46}
QUALITY CHECKLIST (verify before outputting)
{'=' * 46}
[x] 1,000–1,500 words (hard limits)
[x] H1 not in content (WordPress sets it from title)
[x] 4+ internal links — all from greenafrica.co.ke
[x] Focus keyword in opening paragraph and 1+ H2
[x] 7 H3 blocks under "Our Services"
[x] 5 FAQs
[x] Phone + email CTAs present
[x] No US locations, no legal/attorney content
[x] meta_description is 140-160 characters
[x] seo_title is under 60 characters
[x] Valid JSON — no trailing commas, all strings escaped"""


# ── Sitemap reference — elisamotors.co.ke ─────────────────────────────────────
_SITEMAP_ELISAMOTORS = """
HOMEPAGE & CORE:
https://elisamotors.co.ke/

CAR IMPORT — Companies, Agents & Dealers:
https://elisamotors.co.ke/best-car-import-companies-in-kenya/
https://elisamotors.co.ke/best-car-import-agents-nairobi/
https://elisamotors.co.ke/best-reputable-car-import-dealers-in-kenya/
https://elisamotors.co.ke/best-car-importers-in-kenya/
https://elisamotors.co.ke/best-car-import-companies-in-kenya-2/
https://elisamotors.co.ke/best-car-import-companies-in-kenya-3/
https://elisamotors.co.ke/car-import-agents-in-nairobi/
https://elisamotors.co.ke/clearing-and-forwarding-agents-kenya-cars/
https://elisamotors.co.ke/clearing-and-forwarding-agents-in-kenya-for-cars/
https://elisamotors.co.ke/clearing-and-forwarding-agents-in-kenya-for-cars-2/
https://elisamotors.co.ke/car-import-brokerage-kenya/
https://elisamotors.co.ke/authorized-car-dealers-kenya/
https://elisamotors.co.ke/direct-car-dealers-nairobi/
https://elisamotors.co.ke/trusted-car-showrooms-kenya/
https://elisamotors.co.ke/cheapest-car-dealerships-kenya/
https://elisamotors.co.ke/car-bazaars-in-nairobi/

CAR IMPORT — Process, Guides & Documentation:
https://elisamotors.co.ke/import-cars-from-japan-to-kenya/
https://elisamotors.co.ke/import-cars-from-japan-to-kenya-2/
https://elisamotors.co.ke/how-to-import-a-car-to-kenya-from-uk/
https://elisamotors.co.ke/how-to-import-a-car-to-kenya-from-uk-2/
https://elisamotors.co.ke/how-to-import-cars-from-japan-uk-to-kenya/
https://elisamotors.co.ke/import-car-from-dubai-to-kenya/
https://elisamotors.co.ke/import-car-from-germany-to-kenya/
https://elisamotors.co.ke/import-car-from-usa-to-kenya/
https://elisamotors.co.ke/step-by-step-guide-to-importing-a-car-to-kenya/
https://elisamotors.co.ke/car-import-process-step-by-step-in-kenya/
https://elisamotors.co.ke/direct-car-import-from-japan-to-mombasa/
https://elisamotors.co.ke/cheapest-way-to-import-a-car-to-kenya/
https://elisamotors.co.ke/cheapest-way-to-import-a-car-kenya/
https://elisamotors.co.ke/import-car-online-kenya/
https://elisamotors.co.ke/import-car-online-payment-kenya/
https://elisamotors.co.ke/car-import-timeline-kenya/
https://elisamotors.co.ke/documentation-for-car-import-kenya/
https://elisamotors.co.ke/bill-of-lading-car-import-kenya/
https://elisamotors.co.ke/how-to-clear-imported-car-at-mombasa-port/
https://elisamotors.co.ke/port-clearance-fees-mombasa/
https://elisamotors.co.ke/clearing-and-forwarding-charges-mombasa-car/
https://elisamotors.co.ke/vehicle-import-declaration-form-kenya/
https://elisamotors.co.ke/customs-valuation-imported-cars-kenya/
https://elisamotors.co.ke/personal-car-import-kenya/
https://elisamotors.co.ke/commercial-car-import-kenya/

CAR IMPORT — Taxes, Duties & Costs:
https://elisamotors.co.ke/kenya-car-import-duty-calculator/
https://elisamotors.co.ke/kra-car-import-duty-rates/
https://elisamotors.co.ke/car-import-costs-kenya-breakdown/
https://elisamotors.co.ke/car-import-costs-in-kenya/
https://elisamotors.co.ke/car-import-costs-in-kenya-2/
https://elisamotors.co.ke/average-cost-to-import-car-to-kenya/
https://elisamotors.co.ke/excise-duty-on-imported-cars-kenya/
https://elisamotors.co.ke/vat-on-car-imports-kenya/
https://elisamotors.co.ke/idf-fee-car-import-kenya/
https://elisamotors.co.ke/railway-development-levy-car-import-kenya/
https://elisamotors.co.ke/environmental-levy-car-import-kenya/
https://elisamotors.co.ke/import-duty-calculation-used-cars-kenya/
https://elisamotors.co.ke/how-vehicle-import-taxes-are-calculated-in-kenya/
https://elisamotors.co.ke/government-tax-on-imported-cars-kenya/
https://elisamotors.co.ke/luxury-car-import-taxes-kenya/
https://elisamotors.co.ke/electric-car-import-duty-in-kenya/
https://elisamotors.co.ke/hybrid-car-import-duty-kenya/
https://elisamotors.co.ke/import-tax-on-electric-cars-kenya/
https://elisamotors.co.ke/total-cost-of-importing-a-car-from-japan-to-kenya/
https://elisamotors.co.ke/shipping-costs-from-japan-to-kenya-cars/
https://elisamotors.co.ke/shipping-costs-from-uk-to-kenya-cars/

CAR IMPORT — Rules, Regulations & Inspections:
https://elisamotors.co.ke/car-import-regulations-in-kenya-in-2025/
https://elisamotors.co.ke/car-import-age-limit-kenya/
https://elisamotors.co.ke/minimum-age-of-imported-cars-in-kenya/
https://elisamotors.co.ke/left-hand-drive-car-import-rules-kenya/
https://elisamotors.co.ke/right-hand-drive-car-import-kenya/
https://elisamotors.co.ke/pre-shipment-inspection-certificate-kenya-jevic/
https://elisamotors.co.ke/pre-shipment-inspection-certificate-kenya-qisj/
https://elisamotors.co.ke/pre-export-inspection-companies-kenya/
https://elisamotors.co.ke/vehicle-inspection-for-import-in-kenya/
https://elisamotors.co.ke/roadworthiness-certificate-kenya-for-imports/
https://elisamotors.co.ke/roadworthiness-certificate-kenya-for-imports-2/
https://elisamotors.co.ke/used-car-import-restrictions-kenya/
https://elisamotors.co.ke/car-import-restrictions-kenya-2024/
https://elisamotors.co.ke/car-import-rules-for-older-vehicles-in-kenya/
https://elisamotors.co.ke/duty-free-car-import-kenya/
https://elisamotors.co.ke/duty-free-car-import-kenya-for-diplomats/
https://elisamotors.co.ke/diplomat-car-import-kenya-rules/
https://elisamotors.co.ke/diplomat-car-import-kenya-eligibility/
https://elisamotors.co.ke/returning-resident-car-import-exemption-in-kenya/
https://elisamotors.co.ke/temporary-car-import-permit-kenya/
https://elisamotors.co.ke/car-export-from-kenya-rules/
https://elisamotors.co.ke/classic-car-import-rules-in-kenya/
https://elisamotors.co.ke/vintage-car-import-rules-kenya/
https://elisamotors.co.ke/best-shipping-lines-for-car-import-kenya/
https://elisamotors.co.ke/best-shipping-lines-for-car-import-kenya-2/

CAR IMPORT — Registration & NTSA:
https://elisamotors.co.ke/car-registration-process-imported-vehicles-kenya/
https://elisamotors.co.ke/ntsa-import-car-registration-kenya/
https://elisamotors.co.ke/ntsa-motor-vehicle-search-kenya/
https://elisamotors.co.ke/vehicle-verification-imported-car-kenya/
https://elisamotors.co.ke/driving-license-application-kenya/

USED CARS — Japan & UK:
https://elisamotors.co.ke/japanese-used-car-market-in-kenya/
https://elisamotors.co.ke/japanese-used-cars-for-sale-in-kenya/
https://elisamotors.co.ke/japanese-used-cars-for-sale-in-kenya-for-import/
https://elisamotors.co.ke/uk-used-cars-for-sale-in-kenya/
https://elisamotors.co.ke/uk-used-cars-for-sale-in-kenya-2/
https://elisamotors.co.ke/uk-used-cars-for-sale-in-kenya-3/
https://elisamotors.co.ke/uk-used-cars-for-sale-in-kenya-for-import/
https://elisamotors.co.ke/pre-owned-cars-from-japan-in-kenya/
https://elisamotors.co.ke/pre-owned-cars-from-japan-kenya/
https://elisamotors.co.ke/pre-owned-cars-from-japan-for-import-to-kenya/
https://elisamotors.co.ke/cheap-cars-to-import-to-kenya/
https://elisamotors.co.ke/cheap-cars-to-import-to-kenya-2/
https://elisamotors.co.ke/cheap-cars-to-import-to-kenya-3/
https://elisamotors.co.ke/auction-cars-for-import-kenya/
https://elisamotors.co.ke/auction-cars-for-import-kenya-japanese-car-auctions/
https://elisamotors.co.ke/salvage-cars-import-kenya/
https://elisamotors.co.ke/salvage-cars-import-kenya-2/
https://elisamotors.co.ke/salvage-cars-for-import-kenya/
https://elisamotors.co.ke/import-second-hand-cars-in-kenya/
https://elisamotors.co.ke/import-car-with-low-mileage-kenya/
https://elisamotors.co.ke/import-car-with-low-mileage-kenya-2/
https://elisamotors.co.ke/new-car-import-kenya/
https://elisamotors.co.ke/luxury-car-import-kenya/
https://elisamotors.co.ke/best-luxury-car-import-in-kenya/

PRICE PAGES — Toyota:
https://elisamotors.co.ke/best-toyota-prado-price-in-kenya/
https://elisamotors.co.ke/prado-price-in-kenya/
https://elisamotors.co.ke/best-prado-tx-price-in-kenya/
https://elisamotors.co.ke/brand-new-prado-tx-price-in-kenya/
https://elisamotors.co.ke/prado-tx-limited-price-kenya/
https://elisamotors.co.ke/land-cruiser-prado-tx-price-in-kenya/
https://elisamotors.co.ke/land-cruiser-prado-tx-diesel-price-kenya/
https://elisamotors.co.ke/toyota-land-cruiser-prado-trj150-price-kenya/
https://elisamotors.co.ke/toyota-land-cruiser-prado-grj150-price-in-kenya/
https://elisamotors.co.ke/best-toyota-v8-price-in-kenya/
https://elisamotors.co.ke/best-toyota-v8-price-in-kenya-clone/
https://elisamotors.co.ke/v8-price-in-kenya/
https://elisamotors.co.ke/top-v8-price-in-kenya/
https://elisamotors.co.ke/land-cruiser-vx-price-in-kenya/
https://elisamotors.co.ke/land-cruiser-vx-petrol-price-kenya/
https://elisamotors.co.ke/land-cruiser-v8-diesel-for-sale-kenya/
https://elisamotors.co.ke/land-cruiser-v8-diesel-for-sale-kenya-2/
https://elisamotors.co.ke/toyota-land-cruiser-v8-brand-new-price-in-kenya/
https://elisamotors.co.ke/price-ranges-of-toyota-land-cruiser-200-series-in-kenya/
https://elisamotors.co.ke/toyota-land-cruiser-300-series-price-in-kenya/
https://elisamotors.co.ke/toyota-vitz-price-in-kenya-used/
https://elisamotors.co.ke/toyota-probox-price-in-kenya-second-hand/
https://elisamotors.co.ke/toyota-probox-new-model-kenya/
https://elisamotors.co.ke/toyota-rush-price-in-kenya/
https://elisamotors.co.ke/toyota-rush-7-seater-price-in-kenya/
https://elisamotors.co.ke/toyota-fielder-price-in-kenya-used/
https://elisamotors.co.ke/toyota-fielder-hybrid-price-in-kenya/
https://elisamotors.co.ke/toyota-harrier-price-in-kenya-used/
https://elisamotors.co.ke/toyota-harrier-hybrid-price-in-kenya/
https://elisamotors.co.ke/harrier-price-in-kenya/
https://elisamotors.co.ke/toyota-rav4-price-in-kenya/
https://elisamotors.co.ke/toyota-rav4-hybrid-price-in-kenya/
https://elisamotors.co.ke/toyota-c-hr-price-in-kenya/
https://elisamotors.co.ke/toyota-c-hr-hybrid-price-in-kenya/
https://elisamotors.co.ke/toyota-hilux-price-in-kenya/
https://elisamotors.co.ke/toyota-hilux-double-cab-price-kenya/
https://elisamotors.co.ke/toyota-crown-price-in-kenya/
https://elisamotors.co.ke/toyota-crown-majesta-price-in-kenya/
https://elisamotors.co.ke/toyota-noah-price-in-kenya-used/
https://elisamotors.co.ke/toyota-noah-si-price-in-kenya/
https://elisamotors.co.ke/toyota-voxy-price-in-kenya-used/
https://elisamotors.co.ke/toyota-voxy-z-price-in-kenya/
https://elisamotors.co.ke/toyota-venza-price-in-kenya/
https://elisamotors.co.ke/toyota-venza-price-in-kenya-2/
https://elisamotors.co.ke/toyota-aqua-price-in-kenya/
https://elisamotors.co.ke/toyota-prius-price-in-kenya/
https://elisamotors.co.ke/toyota-supra-price-in-kenya/
https://elisamotors.co.ke/toyota-urban-cruiser-price-in-kenya/

PRICE PAGES — Range Rover, Land Rover & Defender:
https://elisamotors.co.ke/best-range-rover-price-in-kenya/
https://elisamotors.co.ke/range-rover-price-in-kenya/
https://elisamotors.co.ke/range-rover-price-in-kenya-2/
https://elisamotors.co.ke/range-rover-price-in-kenya-2025-every-model-every-budget/
https://elisamotors.co.ke/latest-range-rover-price-in-kenya/
https://elisamotors.co.ke/best-range-rover-2025-price-in-kenya/
https://elisamotors.co.ke/range-rover-sport-price-in-kenya/
https://elisamotors.co.ke/best-price-of-range-rover-sport-in-kenya/
https://elisamotors.co.ke/range-rover-sport-autobiography-price-kenya/
https://elisamotors.co.ke/range-rover-sport-hse-price-kenya/
https://elisamotors.co.ke/range-rover-sport-hse-price-kenya-2/
https://elisamotors.co.ke/range-rover-sport-svr-price-kenya/
https://elisamotors.co.ke/range-rover-vogue-for-sale-in-kenya/
https://elisamotors.co.ke/best-range-rover-vogue-price-in-kenya/
https://elisamotors.co.ke/range-rover-autobiography-price-in-kenya/
https://elisamotors.co.ke/range-rover-autobiography-price-in-kenya-2022/
https://elisamotors.co.ke/range-rover-evoque-price-in-kenya/
https://elisamotors.co.ke/range-rover-evoque-r-dynamic-price-in-kenya/
https://elisamotors.co.ke/range-rover-velar-price-in-kenya/
https://elisamotors.co.ke/discovery-4-price-in-kenya/
https://elisamotors.co.ke/discovery-4-hse-in-kenya/
https://elisamotors.co.ke/discovery-sport-price-in-kenya/
https://elisamotors.co.ke/discovery-metropolitan-price-kenya/
https://elisamotors.co.ke/discovery-metropolitan-price-kenya-2/
https://elisamotors.co.ke/discovery-commercial-price-kenya/
https://elisamotors.co.ke/defender-price-in-kenya/
https://elisamotors.co.ke/defender-110-price-in-kenya/
https://elisamotors.co.ke/defender-130-price-in-kenya/
https://elisamotors.co.ke/land-rover-defender-90-price-kenya/

PRICE PAGES — German Luxury (BMW, Audi, Mercedes, VW, Porsche, Volvo):
https://elisamotors.co.ke/best-bmw-price-in-kenya/
https://elisamotors.co.ke/bmw-price-in-kenya/
https://elisamotors.co.ke/bmw-3-series-price-in-kenya/
https://elisamotors.co.ke/bmw-320i-price-in-kenya/
https://elisamotors.co.ke/bmw-5-series-price-in-kenya/
https://elisamotors.co.ke/bmw-530e-price-in-kenya/
https://elisamotors.co.ke/bmw-x1-price-in-kenya/
https://elisamotors.co.ke/bmw-x5-price-in-kenya/
https://elisamotors.co.ke/bmw-x5-xdrive40e-price-in-kenya/
https://elisamotors.co.ke/bmw-x6-m50i-price-in-kenya/
https://elisamotors.co.ke/bmw-x6-price-in-kenya-new-model/
https://elisamotors.co.ke/bmw-1-series-price-in-kenya/
https://elisamotors.co.ke/bmw-2-series-price-in-kenya/
https://elisamotors.co.ke/bmw-m3-price-in-kenya/
https://elisamotors.co.ke/bmw-z4-price-in-kenya/
https://elisamotors.co.ke/brand-new-bmw-330e-prices/
https://elisamotors.co.ke/best-audi-price-in-kenya/
https://elisamotors.co.ke/audi-a3-price-in-kenya/
https://elisamotors.co.ke/audi-a3-sportback-for-sale-kenya/
https://elisamotors.co.ke/audi-a3-sedan-price-kenya/
https://elisamotors.co.ke/brand-new-audi-a4-prices-2024-2025/
https://elisamotors.co.ke/audi-a4-avant-price-in-kenya/
https://elisamotors.co.ke/audi-a5-price-in-kenya/
https://elisamotors.co.ke/audi-q2-price-in-kenya/
https://elisamotors.co.ke/audi-q3-price-in-kenya-2025/
https://elisamotors.co.ke/new-audi-q5-prices-in-kenya/
https://elisamotors.co.ke/best-audi-q5-price-in-kenya/
https://elisamotors.co.ke/best-audi-q5-tfsi-price-in-kenya/
https://elisamotors.co.ke/best-audi-q5-2019-price-in-kenya/
https://elisamotors.co.ke/best-audi-q5-2020-price-in-kenya/
https://elisamotors.co.ke/audi-q5-s-line-price-kenya/
https://elisamotors.co.ke/best-audi-sq5-price-in-kenya/
https://elisamotors.co.ke/audi-q7-prices-in-kenya/
https://elisamotors.co.ke/best-audi-q7-price-in-kenya/
https://elisamotors.co.ke/audi-q7-tfsi-price-kenya/
https://elisamotors.co.ke/best-audi-q8-price-in-kenya/
https://elisamotors.co.ke/audi-rs3-price-in-kenya/
https://elisamotors.co.ke/audi-tt-price-in-kenya/
https://elisamotors.co.ke/best-mercedes-price-in-kenya/
https://elisamotors.co.ke/mercedes-price-in-kenya/
https://elisamotors.co.ke/mercedes-a-class-price-in-kenya/
https://elisamotors.co.ke/mercedes-c-class-price-in-kenya/
https://elisamotors.co.ke/mercedes-benz-c-class-amg-price-kenya/
https://elisamotors.co.ke/mercedes-c200-price-in-kenya/
https://elisamotors.co.ke/mercedes-c250-price-in-kenya/
https://elisamotors.co.ke/mercedes-cla-price-in-kenya/
https://elisamotors.co.ke/mercedes-e-class-price-in-kenya/
https://elisamotors.co.ke/mercedes-e300-price-in-kenya/
https://elisamotors.co.ke/mercedes-s-class-price-in-kenya/
https://elisamotors.co.ke/mercedes-s500-price-in-kenya/
https://elisamotors.co.ke/mercedes-gla-price-in-kenya/
https://elisamotors.co.ke/mercedes-sprinter-price-in-kenya-vans/
https://elisamotors.co.ke/volkswagen-golf-price-in-kenya/
https://elisamotors.co.ke/volkswagen-golf-gti-price-kenya/
https://elisamotors.co.ke/vw-golf-tsi-price-kenya/
https://elisamotors.co.ke/volkswagen-passat-price-in-kenya/
https://elisamotors.co.ke/volkswagen-passat-cc-price-kenya/
https://elisamotors.co.ke/volkswagen-polo-price-in-kenya/
https://elisamotors.co.ke/volkswagen-tiguan-price-in-kenya/
https://elisamotors.co.ke/volkswagen-beetle-for-sale-in-kenya/
https://elisamotors.co.ke/best-porsche-cayenne-price-in-kenya/
https://elisamotors.co.ke/volvo-xc60-price-in-kenya/
https://elisamotors.co.ke/volvo-xc60-r-design-price-kenya/
https://elisamotors.co.ke/volvo-s60-polestar-price-kenya/
https://elisamotors.co.ke/volvo-s90-price-in-kenya/
https://elisamotors.co.ke/volvo-v40-price-in-kenya/
https://elisamotors.co.ke/volvo-v40-price-in-kenya-2/

PRICE PAGES — Japanese (Nissan, Subaru, Mazda, Honda, Mitsubishi, Suzuki, Lexus, Isuzu):
https://elisamotors.co.ke/nissan-note-price-in-kenya/
https://elisamotors.co.ke/nissan-note-e-power-price-kenya/
https://elisamotors.co.ke/nissan-x-trail-price-in-kenya/
https://elisamotors.co.ke/nissan-x-trail-hybrid-price-kenya/
https://elisamotors.co.ke/nissan-juke-price-in-kenya/
https://elisamotors.co.ke/nissan-juke-turbo-price-in-kenya/
https://elisamotors.co.ke/nissan-navara-price-in-kenya/
https://elisamotors.co.ke/nissan-navara-np300-price-in-kenya/
https://elisamotors.co.ke/nissan-skyline-pricing-in-kenya/
https://elisamotors.co.ke/nissan-skyline-gtr-price-kenya/
https://elisamotors.co.ke/nissan-serena-price-in-kenya-used/
https://elisamotors.co.ke/nissan-patrol-price-in-kenya/
https://elisamotors.co.ke/nissan-pathfinder-price-in-kenya/
https://elisamotors.co.ke/nissan-leaf-price-in-kenya/
https://elisamotors.co.ke/nissan-murano-price-in-kenya/
https://elisamotors.co.ke/nissan-gt-r-price-in-kenya/
https://elisamotors.co.ke/nissan-kicks-price-in-kenya/
https://elisamotors.co.ke/nissan-diesel-truck-price-in-kenya/
https://elisamotors.co.ke/subaru-impreza-price-in-kenya/
https://elisamotors.co.ke/subaru-impreza-wrx-sti-price-kenya/
https://elisamotors.co.ke/subaru-forester-price-in-kenya/
https://elisamotors.co.ke/subaru-forester-xt-price-kenya/
https://elisamotors.co.ke/subaru-legacy-price-in-kenya/
https://elisamotors.co.ke/mazda-demio-price-in-kenya/
https://elisamotors.co.ke/mazda-demio-skyactiv-price-kenya/
https://elisamotors.co.ke/best-cx-5-price-in-kenya/
https://elisamotors.co.ke/mazda-cx-5-prices-in-kenya/
https://elisamotors.co.ke/mazda-cx-5-diesel-price-in-kenya/
https://elisamotors.co.ke/best-mazda-cx-5-diesel-price-in-kenya/
https://elisamotors.co.ke/best-mazda-cx-5-petrol-price-in-kenya/
https://elisamotors.co.ke/best-mazda-cx-5-with-sunroof-price-in-kenya/
https://elisamotors.co.ke/mazda-3-price-in-kenya/
https://elisamotors.co.ke/honda-fit-price-in-kenya/
https://elisamotors.co.ke/honda-fit-hybrid-price-in-kenya/
https://elisamotors.co.ke/honda-crv-price-in-kenya/
https://elisamotors.co.ke/honda-crv-2-0-price-kenya/
https://elisamotors.co.ke/honda-vezel-in-kenya/
https://elisamotors.co.ke/honda-vezel-hybrid-price-overview-in-kenya/
https://elisamotors.co.ke/honda-stepwagon-price-in-kenya-used/
https://elisamotors.co.ke/honda-insight-price-in-kenya/
https://elisamotors.co.ke/honda-civic-price-in-kenya/
https://elisamotors.co.ke/mitsubishi-outlander-price-in-kenya/
https://elisamotors.co.ke/mitsubishi-outlander-phev-price-in-kenya/
https://elisamotors.co.ke/mitsubishi-pajero-price-in-kenya/
https://elisamotors.co.ke/mitsubishi-pajero-sport-price-kenya/
https://elisamotors.co.ke/mitsubishi-montero-price-in-kenya/
https://elisamotors.co.ke/mitsubishi-lancer-price-in-kenya/
https://elisamotors.co.ke/mitsubishi-mirage-price-in-kenya/
https://elisamotors.co.ke/mitsubishi-canter-price-in-kenya-trucks/
https://elisamotors.co.ke/suzuki-swift-price-in-kenya/
https://elisamotors.co.ke/suzuki-swift-sports-price-in-kenya/
https://elisamotors.co.ke/suzuki-vitara-price-in-kenya/
https://elisamotors.co.ke/suzuki-vitara-allgrip-price-kenya/
https://elisamotors.co.ke/suzuki-alto-price-in-kenya/
https://elisamotors.co.ke/lexus-rx-price-in-kenya/
https://elisamotors.co.ke/lexus-rx-450h-price-in-kenya/
https://elisamotors.co.ke/lexus-lx-570-price-in-kenya/
https://elisamotors.co.ke/lexus-is-price-in-kenya/
https://elisamotors.co.ke/lexus-nx-price-in-kenya/
https://elisamotors.co.ke/lexus-gs-price-in-kenya/
https://elisamotors.co.ke/lexus-gs-price-in-kenya-2/
https://elisamotors.co.ke/lexus-ls-460-price-in-kenya/
https://elisamotors.co.ke/isuzu-d-max-price-in-kenya/
https://elisamotors.co.ke/isuzu-d-max-single-cab-price-kenya/
https://elisamotors.co.ke/isuzu-mu-x-price-in-kenya/
https://elisamotors.co.ke/isuzu-fx-price-in-kenya-trucks/
https://elisamotors.co.ke/ford-ranger-price-in-kenya/
https://elisamotors.co.ke/ford-ranger-wildtrak-price-kenya/
https://elisamotors.co.ke/ford-everest-price-overview-in-kenya/
https://elisamotors.co.ke/ford-focus-price-in-kenya/

PRICE PAGES — Other Brands (Tesla, BYD, MG, Tata, Mahindra, Peugeot, Renault, Skoda, Chery, Datsun, Proton, GW):
https://elisamotors.co.ke/tesla-model-3-price-in-kenya/
https://elisamotors.co.ke/byd-atto-3-price-in-kenya/
https://elisamotors.co.ke/byd-f3-price-in-kenya/
https://elisamotors.co.ke/mg-zs-price-in-kenya/
https://elisamotors.co.ke/tata-safari-price-in-kenya/
https://elisamotors.co.ke/mahindra-scorpio-price-in-kenya/
https://elisamotors.co.ke/peugeot-3008-price-in-kenya/
https://elisamotors.co.ke/renault-kwid-price-in-kenya/
https://elisamotors.co.ke/skoda-superb-price-in-kenya/
https://elisamotors.co.ke/chery-qq-price-in-kenya/
https://elisamotors.co.ke/datsun-go-price-in-kenya/
https://elisamotors.co.ke/proton-savvy-price-in-kenya/
https://elisamotors.co.ke/great-wall-wingle-price-in-kenya/
https://elisamotors.co.ke/classic-mini-cooper-price-in-kenya/

CAR USE-CASE & BUYER GUIDES:
https://elisamotors.co.ke/durable-cars-for-kenyan-roads/
https://elisamotors.co.ke/fuel-efficient-cars-in-kenya/
https://elisamotors.co.ke/cars-with-good-resale-value-in-kenya/
https://elisamotors.co.ke/cars-with-cheap-spare-parts-kenya/
https://elisamotors.co.ke/cars-for-taxi-business-kenya/
https://elisamotors.co.ke/cars-for-ride-hailing-kenya/
https://elisamotors.co.ke/best-car-for-long-distance-travel-in-kenya/
https://elisamotors.co.ke/automatic-cars-for-sale-kenya/
https://elisamotors.co.ke/automatic-cars-for-sale-kenya-2/
https://elisamotors.co.ke/manual-cars-for-sale-kenya/
https://elisamotors.co.ke/manual-cars-for-sale-kenya-2/
https://elisamotors.co.ke/diesel-cars-for-sale-kenya/
https://elisamotors.co.ke/diesel-cars-for-sale-kenya-2/
https://elisamotors.co.ke/petrol-cars-for-sale-kenya/
https://elisamotors.co.ke/petrol-cars-for-sale-kenya-2/
https://elisamotors.co.ke/4x4-vehicles-for-sale-kenya/
https://elisamotors.co.ke/all-wheel-drive-cars-kenya/
https://elisamotors.co.ke/front-wheel-drive-cars-kenya/
https://elisamotors.co.ke/rear-wheel-drive-cars-kenya/
https://elisamotors.co.ke/turbocharged-cars-kenya/
https://elisamotors.co.ke/supercharged-cars-kenya/

CAR FEATURES & ACCESSORIES:
https://elisamotors.co.ke/panoramic-sunroof-cars-kenya/
https://elisamotors.co.ke/leather-interior-cars-kenya/
https://elisamotors.co.ke/heated-seats-cars-kenya/
https://elisamotors.co.ke/cooled-seats-cars-kenya/
https://elisamotors.co.ke/infotainment-system-cars-kenya/
https://elisamotors.co.ke/android-auto-apple-carplay-cars-kenya/
https://elisamotors.co.ke/reverse-camera-cars-kenya/
https://elisamotors.co.ke/parking-sensors-cars-kenya/
https://elisamotors.co.ke/blind-spot-monitoring-cars-kenya/
https://elisamotors.co.ke/lane-keep-assist-cars-kenya/
https://elisamotors.co.ke/automatic-emergency-braking-cars-kenya/
https://elisamotors.co.ke/multiple-airbags-cars-kenya/
https://elisamotors.co.ke/abs-braking-system-cars-kenya/
https://elisamotors.co.ke/traction-control-cars-kenya/
https://elisamotors.co.ke/stability-control-cars-kenya/
https://elisamotors.co.ke/push-button-start-cars-kenya/
https://elisamotors.co.ke/keyless-entry-cars-kenya/
https://elisamotors.co.ke/adaptive-cruise-control-cars-kenya/
https://elisamotors.co.ke/electric-power-steering-cars-kenya/
https://elisamotors.co.ke/power-windows-cars-kenya/
https://elisamotors.co.ke/central-locking-cars-kenya/
https://elisamotors.co.ke/alloy-wheels-cars-kenya/
https://elisamotors.co.ke/fog-lights-cars-kenya/
https://elisamotors.co.ke/led-headlights-cars-kenya/
https://elisamotors.co.ke/xenons-headlights-cars-kenya/
https://elisamotors.co.ke/daytime-running-lights-cars-kenya/
https://elisamotors.co.ke/roof-rails-cars-kenya/
https://elisamotors.co.ke/side-steps-cars-kenya/
https://elisamotors.co.ke/tow-bar-cars-kenya/
https://elisamotors.co.ke/tinted-windows-cars-kenya/
https://elisamotors.co.ke/dual-zone-climate-control-cars-kenya/
https://elisamotors.co.ke/rear-seat-entertainment-cars-kenya/
https://elisamotors.co.ke/usb-charging-ports-cars-kenya/
https://elisamotors.co.ke/bluetooth-connectivity-cars-kenya/
https://elisamotors.co.ke/gps-navigation-cars-kenya/
https://elisamotors.co.ke/wireless-phone-charging-cars-kenya/
https://elisamotors.co.ke/car-dash-cams-kenya/
https://elisamotors.co.ke/car-alarms-installation-kenya/
https://elisamotors.co.ke/car-tracking-system-kenya/
https://elisamotors.co.ke/remote-start-car-installation-kenya/

CAR SERVICES — Finance, Insurance, Detailing, Rental, Parts:
https://elisamotors.co.ke/car-financing-options-in-kenya/
https://elisamotors.co.ke/car-loan-requirements-in-kenya/
https://elisamotors.co.ke/trade-in-car-value-in-kenya/
https://elisamotors.co.ke/car-valuation-services-kenya/
https://elisamotors.co.ke/car-insurance-kenya-comparison/
https://elisamotors.co.ke/comprehensive-car-insurance-kenya/
https://elisamotors.co.ke/third-party-car-insurance-kenya/
https://elisamotors.co.ke/genuine-car-parts-kenya/
https://elisamotors.co.ke/aftermarket-car-parts-in-kenya/
https://elisamotors.co.ke/car-accessories-shop-kenya/
https://elisamotors.co.ke/car-detailing-services-kenya/
https://elisamotors.co.ke/car-wash-services-kenya/
https://elisamotors.co.ke/car-servicing-centers-kenya/
https://elisamotors.co.ke/long-term-car-rental-kenya/
https://elisamotors.co.ke/car-rental-kenya-rates/
https://elisamotors.co.ke/car-hire-with-driver-kenya/
https://elisamotors.co.ke/luxury-car-hire-kenya/
https://elisamotors.co.ke/self-drive-car-hire-kenya/
https://elisamotors.co.ke/car-driving-schools-kenya/
https://elisamotors.co.ke/genuine-toyota-parts-dealers-in-kenya/
https://elisamotors.co.ke/genuine-subaru-parts-dealers-kenya/
https://elisamotors.co.ke/genuine-bmw-parts-dealers-kenya/
https://elisamotors.co.ke/genuine-audi-parts-dealers-kenya/
https://elisamotors.co.ke/genuine-mercedes-parts-dealers-kenya/
https://elisamotors.co.ke/car-parts-dismantling-in-kenya/
https://elisamotors.co.ke/car-spare-parts-shop-kariobangi/
https://elisamotors.co.ke/kariobangi-car-parts-import-kenya/

PERFORMANCE & ENTHUSIAST:
https://elisamotors.co.ke/performance-car-modifications-in-kenya/
https://elisamotors.co.ke/car-tuning-services-in-kenya/
https://elisamotors.co.ke/rally-cars-available-in-kenya/
https://elisamotors.co.ke/drift-cars-for-sale-kenya/
https://elisamotors.co.ke/racing-cars-for-sale-kenya/
https://elisamotors.co.ke/featured-automobile-clubs-in-kenya/
https://elisamotors.co.ke/car-shows-events-kenya/
https://elisamotors.co.ke/formula-one-cars-in-kenya/
https://elisamotors.co.ke/youtube-car-reviews-kenya/
https://elisamotors.co.ke/project-cars-for-sale-in-kenya/
https://elisamotors.co.ke/vintage-cars-for-restoration-in-kenya/

EMERGING TECH:
https://elisamotors.co.ke/hydrogen-fuel-cell-cars-in-kenya/
https://elisamotors.co.ke/the-future-of-self-driving-cars-in-kenya/
https://elisamotors.co.ke/flying-cars-in-kenya/
https://elisamotors.co.ke/solar-powered-cars-in-kenya/

MARKETPLACES & COMPETITION REFERENCE:
https://elisamotors.co.ke/motors-kenya-cars-for-sale/
https://elisamotors.co.ke/jiji-kenya-cars-for-sale/
https://elisamotors.co.ke/cheki-kenya-used-cars/
https://elisamotors.co.ke/pre-order-cars-kenya/
"""


_ELISAMOTORS_LOCATIONS = [
    "Nairobi", "Mombasa", "Kisumu", "Nakuru", "Eldoret",
    "Thika", "Nyeri", "Machakos", "Naivasha", "Kitengela",
    "Karen", "Westlands", "Kilimani", "Ruiru", "Kiambu",
    "Mlolongo", "Kariobangi", "Mombasa Road", "Industrial Area Nairobi",
    "Meru", "Kakamega", "Kisii",
]

_ELISAMOTORS_SERVICE_CATEGORIES = [
    "Car Import from Japan",
    "Car Import from UK",
    "Car Import from Dubai, Germany & USA",
    "Clearing & Forwarding at Mombasa Port",
    "KRA Import Duty Calculation & Tax Advisory",
    "NTSA Registration & Roadworthiness",
    "Pre-shipment Inspection (JEVIC / QISJ)",
    "Direct Car Dealership & Showroom Sales",
    "Pre-Order & Auction Sourcing (Japan / UK)",
    "Car Financing, Insurance & Trade-In",
    "Genuine Spare Parts & After-Sales Service",
    "Luxury, Salvage & Classic Car Imports",
]

_ELISAMOTORS_COMPANY = {
    "name":    "Elisa Motors",
    "phone_1": "",
    "phone_2": "",
    "email":   "info@elisamotors.co.ke",
    "address": "Nairobi, Kenya",
    "hours":   "Monday to Saturday, 8:00 AM to 6:00 PM",
    "whatsapp_label": "Chat on WhatsApp",
}

_ELISAMOTORS_INTERNAL_LINK_HUBS = """
HOMEPAGE / PARENT:        https://elisamotors.co.ke/
IMPORT GUIDES (parent):   https://elisamotors.co.ke/step-by-step-guide-to-importing-a-car-to-kenya/
IMPORT DUTY CALCULATOR:   https://elisamotors.co.ke/kenya-car-import-duty-calculator/
IMPORT COSTS BREAKDOWN:   https://elisamotors.co.ke/car-import-costs-kenya-breakdown/
IMPORT FROM JAPAN:        https://elisamotors.co.ke/import-cars-from-japan-to-kenya/
IMPORT FROM UK:           https://elisamotors.co.ke/how-to-import-a-car-to-kenya-from-uk/
CLEARING & FORWARDING:    https://elisamotors.co.ke/clearing-and-forwarding-agents-in-kenya-for-cars/
PORT CLEARANCE MOMBASA:   https://elisamotors.co.ke/how-to-clear-imported-car-at-mombasa-port/
NTSA REGISTRATION:        https://elisamotors.co.ke/ntsa-import-car-registration-kenya/
JAPAN USED CAR MARKET:    https://elisamotors.co.ke/japanese-used-car-market-in-kenya/
UK USED CARS FOR SALE:    https://elisamotors.co.ke/uk-used-cars-for-sale-in-kenya/
BEST IMPORT COMPANIES:    https://elisamotors.co.ke/best-car-import-companies-in-kenya/
BEST IMPORT AGENTS:       https://elisamotors.co.ke/best-car-import-agents-nairobi/
DIRECT DEALERS NAIROBI:   https://elisamotors.co.ke/direct-car-dealers-nairobi/
"""


def _build_elisamotors_system_prompt(cta_email: str) -> str:
    company = _ELISAMOTORS_COMPANY
    services = "\n  - " + "\n  - ".join(_ELISAMOTORS_SERVICE_CATEGORIES)
    locations = ", ".join(_ELISAMOTORS_LOCATIONS)
    phone_block = (
        f"Phone:   {company['phone_1']}  |  {company['phone_2']}"
        if company['phone_1'] else "Phone:   (configure via .env / template)"
    )
    return f"""You are an expert SEO content writer for Elisa Motors
(https://elisamotors.co.ke) — a Kenyan car import, dealership, and clearing-and-forwarding
company helping Kenyans import, buy, and finance vehicles from Japan, UK, Dubai, Germany,
and the USA. Based in {company['address']}, with port operations at Mombasa.

You write for Kenyan car buyers, importers, fleet managers, taxi/ride-hailing operators,
returning residents, diplomats, and dealers. Tone is professional, trustworthy,
locally relevant, and conversion-focused. DO NOT write about US law, lawyers,
attorneys, or agriculture — this is NOT a legal or agri site.

{'=' * 46}
COMPANY DETAILS (use these verbatim where applicable)
{'=' * 46}
Name:    {company['name']}
{phone_block}
Email:   {company['email']}    (alt CTA email: {cta_email})
Address: {company['address']}
Hours:   {company['hours']}

{'=' * 46}
CORE SERVICE CATEGORIES (pick the most relevant for the focus keyword)
{'=' * 46}{services}

{'=' * 46}
TARGET LOCATIONS (sprinkle these Kenyan towns / Nairobi suburbs naturally)
{'=' * 46}
{locations}

{'=' * 46}
INTERNAL LINK LIBRARY — full sitemap (elisamotors.co.ke ONLY)
{'=' * 46}
Use ONLY these real Elisa Motors URLs as internal links. Select 20+ that are most
thematically relevant to the focus keyword (mix: parent hubs, model price pages,
import-process pages, related buyer guides, location/dealer pages, feature pages,
parts/services). Anchor text must be natural and descriptive, never raw URLs.
DO NOT invent URLs. DO NOT link to any external/legal/lawyer/agri site.

KEY HUBS (link to several of these in every article):
{_ELISAMOTORS_INTERNAL_LINK_HUBS}

FULL SITEMAP:
{_SITEMAP_ELISAMOTORS}

{'=' * 46}
OUTPUT FORMAT — STRICT JSON ONLY
{'=' * 46}
Return ONLY a valid JSON object. No text before or after. No markdown fences.

{{
  "title": "SEO-optimized H1 (focus keyword early, under 70 chars total)",
  "slug": "url-friendly-slug-matching-title",
  "meta_description": "150-160 chars — include focus keyword, Kenya/location, CTA",
  "seo_title": "Under 60 chars — keyword near the start",
  "focus_keyphrase": "exact focus keyword or closest natural variant",
  "excerpt": "2-3 sentence hook — keyword in first sentence",
  "categories": ["1-2 categories from the service list above"],
  "tags": ["10-15 tags: focus keyword, car make/model, Kenyan cities, LSI terms"],
  "content": "FULL HTML blog post — see content rules below"
}}

{'=' * 46}
CONTENT RULES
{'=' * 46}

LENGTH & STRUCTURE
- Minimum 2,400 words of readable text (not counting HTML tags)
- H1 = post title (set by WordPress — do NOT repeat it inside content)
- Use H2 for major sections, H3 for subsections
- No section may exceed 300 words before a new subheading
- No paragraph may exceed 200 words
- 75%+ of sentences must be under 20 words
- Prefer short paragraphs and flowing prose; minimal bullet points

KEYWORD & LSI USAGE
- Focus keyword in opening paragraph, in at least one H2, and naturally 3-5x
- Keyword density at most 2.5%
- Geographic modifiers — sprinkle Kenyan cities, towns, and Nairobi suburbs:
  Nairobi, Mombasa, Kisumu, Nakuru, Eldoret, Thika, Machakos, Karen, Westlands,
  Kilimani, Mlolongo, Ruiru, Kiambu, Kariobangi, Mombasa Road, Industrial Area
- Target one service in multiple locations AND multiple services in one location
  so a single page can rank for many [Service + Location] combinations
- Weave in LSI terms: car import duty Kenya, KRA, NTSA, JEVIC, QISJ, Mombasa port,
  CIF value, IDF fee, RDL, excise duty, VAT, customs valuation, bill of lading,
  pre-shipment inspection, roadworthiness certificate, clearing and forwarding,
  car bazaar, used cars Kenya, Japanese imports, UK imports, right-hand drive

INTERNAL LINKS (CRITICAL — 20+ REQUIRED, ELISAMOTORS URLS ONLY)
- Embed 20 or more internal links using <a href="URL">anchor text</a>
- Pick URLs from the INTERNAL LINK LIBRARY above (full sitemap) that are
  topically related to the focus keyword
- Distribute throughout: intro, services, locations, FAQ, conclusion
- Every "Our Services" H3 must contain at least one internal link
- Anchor text must be natural phrases, never raw URLs
- Always include at least one link to the homepage and one to a parent hub
- NEVER link to greenafrica.co.ke, legal-counsel.net, american-counsel.com,
  or any external/competitor domain

LOCAL SEO ELEMENTS
- Reference Kenyan landmarks where relevant: Mombasa Port (Kilindini), JKIA,
  Nairobi Expressway, Mombasa Road, Thika Superhighway, Industrial Area
- Mention service area: "We serve clients across Kenya including Nairobi,
  Mombasa, Kisumu, Eldoret, Nakuru, Thika, and Mombasa Road"
- Sprinkle nearby communities (Karen, Westlands, Kilimani, Kiambu, Ruiru,
  Mlolongo, Kariobangi) when discussing Nairobi-area services

CONTENT SECTIONS (in this order)
1. Introduction (150-220 words)
   - Open with the practical problem or opportunity the reader is facing
   - Focus keyword in the first two sentences
   - Mention Elisa Motors, Kenya, and 2-3 target locations
   - End with a phone/WhatsApp CTA and link to the homepage

2. Why {{Topic}} Matters in Kenya (H2)
   - 2-3 paragraphs on relevance to Kenya's car market, KRA duty regime,
     Mombasa port logistics, or current consumer trends
   - Reference at least 2 Kenyan cities; weave in 2+ LSI keywords
   - Link to the import duty calculator or costs breakdown page

3. Our Services: {{Service / Topic}} Across Kenya (H2)
   - EXACTLY 7 H3 sub-sections, each covering one of:
     * Car import from Japan
     * Car import from UK / Europe / Dubai / USA (pick one)
     * Clearing & forwarding at Mombasa Port
     * KRA duty calculation & tax advisory
     * NTSA registration & roadworthiness
     * Direct showroom sales / pre-order sourcing
     * Financing, insurance & trade-in OR genuine spare parts
   - Each H3: 2-3 short paragraphs (each under 200 words)
   - Reference a different Kenyan city/suburb in each H3 block
   - At least one H3 must include the primary focus keyword
   - Each H3 must contain at least one internal link from the sitemap

4. Elisa Motors: Serving Major Cities Across Kenya (H2)
   - One short flowing paragraph (3-5 sentences) per city
   - Cover at least 6 cities from the location list
   - Mention a specific service or local context per city
   - No bullet points — write in prose
   - Insert at least one link to the homepage or a parent hub

5. Why Choose Elisa Motors for {{Topic}}? (H2)
   - 4-5 short paragraphs, each highlighting one USP:
     local KRA/NTSA expertise, end-to-end Japan/UK sourcing, transparent quoting,
     Mombasa port clearing partnerships, proven import track record
   - Each paragraph under 200 words
   - Use transition words between paragraphs
   - Include at least one internal link inside this section

6. How to Get Started with {{Topic}} in {{Location}} (H2)
   - 1-2 paragraphs explaining the engagement steps
   - Include phone (or WhatsApp CTA if phone empty), email, address, hours
   - Add internal links to homepage and at least one services/process page
   - End with a strong CTA — "Chat with Elisa Motors on WhatsApp" or
     "Email info@elisamotors.co.ke today"

7. Frequently Asked Questions About {{Topic}} in Kenya (H2)
   - EXACTLY 5 Q&A pairs using <strong>Q:</strong> and <p>A:</p> format
   - Questions must target featured-snippet queries
     (how much, how long, what is, can I, do I need)
   - Each answer 40-100 words
   - Mention Elisa Motors in at least one answer
   - Include 2 internal links inside the FAQ block

8. Contact Elisa Motors Today (H2 / closing CTA)
   - 1 short closing paragraph (3-5 sentences, under 120 words)
   - Reinforce CTA with company name, focus keyword, primary city,
     phone/WhatsApp, and a link to the homepage

CONTACT BLOCK / CTA TEMPLATE
- Email CTA: <strong>Email: <a href="mailto:{company['email']}">{company['email']}</a></strong>
- If phone is configured, use a <strong>Call: <a href="tel:NUMBER">NUMBER</a></strong> line.
- WhatsApp CTA (use placeholder phone — user will update later):
  <strong><a href="https://wa.me/254000000000">Chat on WhatsApp</a></strong>
- Address line: {company['address']}

TRANSITION WORDS (30%+ of sentences must contain one)
Additionally, Furthermore, Moreover, Therefore, However, Meanwhile,
Subsequently, Consequently, For instance, For example, Similarly, Likewise,
As a result, In fact, Conversely, Nevertheless

DO NOT INCLUDE
- No US states/cities, no lawyers, no attorneys, no legal-counsel/agri content
- No links outside elisamotors.co.ke
- No fabricated phone numbers (only real ones provided here)
- No fabricated prices/quotes — speak in ranges and direct readers to enquire

{'=' * 46}
QUALITY CHECKLIST (verify before outputting)
{'=' * 46}
[x] 2,400+ words
[x] H1 not in content (WordPress sets it from title field)
[x] 20+ internal links — all from elisamotors.co.ke
[x] Focus keyword in opening paragraph and 1+ H2
[x] 7 H3 blocks under "Our Services"
[x] 5 FAQs
[x] Email CTA + WhatsApp / phone CTA present
[x] Geographic modifiers (Kenyan cities) throughout
[x] No US locations, no legal/attorney/agri content
[x] meta_description is 150-160 characters
[x] seo_title is under 60 characters
[x] Valid JSON — no trailing commas, all strings escaped"""


def _build_system_prompt(site_domain: str, site_name: str, sitemap_urls: str, cta_email: str) -> str:
    return f"""You are an expert SEO content writer and legal content specialist for the website {site_domain}.
You write for people urgently needing legal help across the United States.
Your tone is professional, empathetic, and urgent but calm.

{'=' * 46}
INTERNAL LINK LIBRARY ({site_domain})
{'=' * 46}
Use ONLY these real URLs as internal links. Select 20+ that are most thematically
relevant to the given keyword. Anchor text must be natural and descriptive.

{sitemap_urls}

{'=' * 46}
OUTPUT FORMAT — STRICT JSON ONLY
{'=' * 46}
Return ONLY a valid JSON object. No text before or after. No markdown fences.

{{
  "title": "SEO-optimized H1 (keyword in first 60 chars, under 70 chars total)",
  "slug": "url-friendly-slug-matching-title",
  "meta_description": "155-160 chars — include focus keyword, compelling CTA",
  "seo_title": "Under 60 chars — keyword near the start",
  "focus_keyphrase": "exact focus keyword or closest natural variant",
  "excerpt": "2-3 sentence hook — keyword in first sentence",
  "categories": ["2-3 relevant category names"],
  "tags": ["10-15 relevant tags including keyword, service type, locations"],
  "content": "FULL HTML blog post — see content rules below"
}}

{'=' * 46}
CONTENT RULES
{'=' * 46}

LENGTH & STRUCTURE
- Minimum 2,400 words of readable text (not counting HTML tags)
- H1 = post title (set by WordPress — do NOT repeat it inside content)
- Use H2 for major sections, H3 for subsections
- No section may exceed 300 words before a new subheading
- No paragraph may exceed 200 words
- 75%+ of sentences must be under 20 words
- Minimal bullet points — prefer short paragraphs and numbered lists

KEYWORD & LSI USAGE
- Focus keyword appears in: opening paragraph, at least one H2, and naturally 3-5x
- Weave in LSI/semantic variants throughout (find relevant terms from context)
- Geographic modifiers: blend the service with US cities/states naturally
  (e.g. "residents of Alabama, Texas, New York, California, and Florida")
- Target one service in multiple locations AND multiple services in one location
  so a single page can rank for many [Service + Location] combinations

INTERNAL LINKS (CRITICAL — 20+ REQUIRED)
- Embed 20 or more internal links using <a href="URL">anchor text</a>
- Pick URLs from the INTERNAL LINK LIBRARY above that are topically related
- Distribute links throughout the post — not all in one section
- Anchor text must be natural phrases, never raw URLs
- Link to: homepage context ({site_domain}), related service pages, nearby
  topic pages, and 2-4 links in the FAQ and conclusion sections

CONTENT SECTIONS (in this order):
1. Introduction (150-200 words)
   - Open with the pain point the reader is facing RIGHT NOW
   - Include focus keyword in the first two sentences
   - End with a transition into the body

2. "Our Services" Section
   - H2: "Our [Service] Services"
   - 7 H3 sub-sections, each covering a specific service variant or location angle
   - Each H3 block: 2-4 paragraphs, all under 200 words
   - Mention specific US locations (cities, counties, states) in each block
   - Include at least one internal link per H3 block

3. Why Choose {site_name} (1 H2 section)
   - 3-4 paragraphs on trust, experience, results
   - Include an email CTA: <strong>Email us: <a href="mailto:{cta_email}">{cta_email}</a></strong>

4. How the Process Works (1 H2 section)
   - Numbered list of 4-6 steps
   - Keep each step to 1-2 sentences

5. FAQ Section
   - H2: "Frequently Asked Questions"
   - Exactly 5 Q&A pairs using <strong>Q:</strong> and <p>A:</p> format
   - Questions must target featured-snippet-style queries (how, what, when, can I)
   - Each answer: 40-80 words
   - Include 2 internal links within the FAQ block

6. Conclusion + CTA (150-200 words)
   - Summarise the urgency
   - Email CTA: <strong>Email us at <a href="mailto:{cta_email}">{cta_email}</a></strong>
   - Include 2-3 internal links

7. Legal Disclaimer (always last)
   - H2: "Legal Disclaimer"
   - 2-3 sentences: content is informational only, not legal advice, consult an attorney

LOCAL SEO ELEMENTS
- Sprinkle US geographic modifiers throughout: state names, major cities, counties
- Reference local landmarks or courts where relevant (e.g. "Cook County Circuit Court")
- Mention service area: "We serve clients across [state] including [city1], [city2], [city3]"

TRANSITION WORDS (30%+ of sentences must open with or contain):
Additionally, Furthermore, Moreover, Therefore, However, Meanwhile,
Subsequently, Consequently, For instance, For example, Similarly, Likewise,
As a result, In fact, Conversely, Nevertheless, On the other hand

CTA
Use this email address for all CTAs: {cta_email}
Do NOT include phone numbers, WhatsApp links, or physical addresses.

{'=' * 46}
QUALITY CHECKLIST (verify before outputting)
{'=' * 46}
[x] 2,400+ words
[x] H1 not in content (WordPress sets it from title field)
[x] 20+ internal links from the library above
[x] Focus keyword in opening paragraph
[x] 7 H3 blocks under "Our Services"
[x] 5 FAQs
[x] Email CTA present ({cta_email})
[x] No phone numbers or WhatsApp links
[x] Legal disclaimer at end
[x] No paragraph over 200 words
[x] 75%+ sentences under 20 words
[x] meta_description is 155-160 characters
[x] seo_title is under 60 characters
[x] Valid JSON — no trailing commas, all strings escaped"""


# Build the active system prompt based on the configured SITE
if SITE == "american-counsel":
    SYSTEM_PROMPT = _build_system_prompt(
        site_domain="american-counsel.com",
        site_name="American Counsel",
        sitemap_urls=_SITEMAP_AMERICAN_COUNSEL,
        cta_email=CTA_EMAIL,
    )
elif SITE == "greenafrica":
    SYSTEM_PROMPT = _build_greenafrica_system_prompt(cta_email=CTA_EMAIL)
elif SITE == "elisamotors":
    SYSTEM_PROMPT = _build_elisamotors_system_prompt(cta_email=CTA_EMAIL)
else:
    SYSTEM_PROMPT = _build_system_prompt(
        site_domain="legal-counsel.net",
        site_name="Legal Counsel",
        sitemap_urls=_SITEMAP_LEGAL_COUNSEL,
        cta_email=CTA_EMAIL,
    )

REQUIRED_FIELDS = [
    "title",
    "slug",
    "meta_description",
    "content",
    "categories",
    "tags",
    "focus_keyphrase",
    "seo_title",
    "excerpt",
]


def _extract_json(text: str) -> str:
    """Strip markdown fences and extract the first {...} block."""
    text = re.sub(r"^```(?:json)?\s*", "", text.strip(), flags=re.IGNORECASE)
    text = re.sub(r"\s*```$", "", text.strip())
    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end == -1:
        raise ValueError("No JSON object found in Claude response")
    return text[start : end + 1]


def validate_content(data: dict[str, Any]) -> None:
    missing = [f for f in REQUIRED_FIELDS if f not in data]
    if missing:
        raise ValueError(f"Missing required fields in Claude response: {missing}")

    is_greenafrica = SITE == "greenafrica"
    link_target   = 4    if is_greenafrica else 20
    link_warn_at  = 3    if is_greenafrica else 15
    meta_min      = 140  if is_greenafrica else 120

    content = data.get("content", "")

    if is_greenafrica:
        plain_text = re.sub(r"<[^>]+>", " ", content)
        word_count = len(plain_text.split())
        if word_count < 1000:
            raise ValueError(
                f"Greenafrica post is too short ({word_count} words). Minimum is 1000."
            )
        if word_count > 1500:
            raise ValueError(
                f"Greenafrica post is too long ({word_count} words). Maximum is 1500."
            )
    elif len(content) < 3000:
        raise ValueError(
            f"Generated content is too short ({len(content)} chars). Expected 3000+ chars."
        )

    link_count = content.count("<a href=")
    if link_count < link_warn_at:
        log.warning(
            f"Only {link_count} internal links found (target is {link_target}+). "
            "Post will still be created."
        )

    if is_greenafrica and re.search(r"legal-counsel\.net|american-counsel\.com", content):
        raise ValueError(
            "Greenafrica content must not link to legal-counsel.net or american-counsel.com."
        )

    if SITE == "elisamotors" and re.search(
        r"legal-counsel\.net|american-counsel\.com|greenafrica\.co\.ke", content
    ):
        raise ValueError(
            "Elisa Motors content must not link to legal-counsel.net, "
            "american-counsel.com, or greenafrica.co.ke."
        )

    if not isinstance(data.get("categories"), list):
        raise ValueError("'categories' must be a list")

    if not isinstance(data.get("tags"), list):
        raise ValueError("'tags' must be a list")

    meta = data.get("meta_description", "")
    if len(meta) < meta_min or len(meta) > 165:
        raise ValueError(
            f"meta_description length {len(meta)} is outside {meta_min}-165 char range."
        )

    seo_title = data.get("seo_title", "")
    if len(seo_title) > 65:
        raise ValueError(
            f"seo_title is {len(seo_title)} chars — must be under 65."
        )


def generate_content(keyword: str) -> dict[str, Any]:
    """Call Claude and return validated structured post data."""
    log.info("Generating content with Claude...")

    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

    message = client.messages.create(
        model=CLAUDE_MODEL,
        max_tokens=CLAUDE_MAX_TOKENS,
        system=SYSTEM_PROMPT,
        messages=[
            {
                "role": "user",
                "content": (
                    f'Write a complete, publish-ready WordPress blog post for '
                    f'this focus keyword: "{keyword}"\n\n'
                    f'Remember: return ONLY valid JSON, no text before or after.'
                ),
            }
        ],
    )

    raw = message.content[0].text

    # ── Token usage ───────────────────────────────────────────────────────────
    usage = message.usage
    input_tokens  = usage.input_tokens
    output_tokens = usage.output_tokens
    total_tokens  = input_tokens + output_tokens
    # Approximate cost for claude-sonnet-4-6: $3/M input, $15/M output
    est_cost_usd  = (input_tokens * 3 + output_tokens * 15) / 1_000_000
    log.info(
        f"Tokens used — input: {input_tokens:,}  output: {output_tokens:,}  "
        f"total: {total_tokens:,}  est. cost: ${est_cost_usd:.4f}"
    )

    log.debug(f"Raw Claude response length: {len(raw)} chars")

    json_str = _extract_json(raw)
    try:
        data = json.loads(json_str, strict=False)
    except json.JSONDecodeError as exc:
        log.warning(f"Standard JSON parse failed ({exc}). Attempting auto-repair...")
        from json_repair import repair_json
        data = json.loads(repair_json(json_str))
    validate_content(data)

    data["_token_usage"] = {
        "input_tokens":  input_tokens,
        "output_tokens": output_tokens,
        "total_tokens":  total_tokens,
        "est_cost_usd":  round(est_cost_usd, 4),
    }

    log.info(f'Content generated: "{data["title"]}"')
    return data
