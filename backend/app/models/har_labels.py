"""
Human Action Recognition (HAR) 15-Class Registry & Taxonomy Metadata
Derived from the Kaggle Dataset: meetnagadia/human-action-recognition-har-dataset
"""

from typing import Dict, Any, List

HAR_CLASSES: List[str] = [
    "calling",
    "clapping",
    "cycling",
    "dancing",
    "drinking",
    "eating",
    "fighting",
    "hugging",
    "laughing",
    "listeningtomusic",
    "running",
    "sitting",
    "sleeping",
    "texting",
    "using_laptop"
]

HAR_CATEGORIES: Dict[str, List[str]] = {
    "Productive & Desk": ["using_laptop", "sitting"],
    "Communication & Device": ["calling", "texting", "listeningtomusic"],
    "Wellness & Sustenance": ["drinking", "eating", "sleeping", "laughing"],
    "Dynamic Movement": ["running", "cycling", "dancing"],
    "Social & Security": ["fighting", "hugging", "clapping"]
}

CLASS_METADATA: Dict[str, Dict[str, Any]] = {
    "calling": {
        "index": 0,
        "name": "Calling",
        "category": "Communication & Device",
        "severity": "normal",
        "color": "#38bdf8",  # Sky blue
        "icon": "phone-call",
        "description": "Holding a phone or receiver against the ear with one hand raised to the head.",
        "associated_objects": ["smartphone", "phone receiver"],
        "posture_cues": ["arm raised to ear", "head slightly tilted", "one-handed grasp"]
    },
    "clapping": {
        "index": 1,
        "name": "Clapping",
        "category": "Social & Security",
        "severity": "info",
        "color": "#a855f7",  # Purple
        "icon": "hands-clapping",
        "description": "Both palms brought together in repetitive impact in front of torso.",
        "associated_objects": ["none"],
        "posture_cues": ["palms opposing", "elbows bent", "hands positioned mid-chest"]
    },
    "cycling": {
        "index": 2,
        "name": "Cycling",
        "category": "Dynamic Movement",
        "severity": "normal",
        "color": "#06b6d4",  # Cyan
        "icon": "bike",
        "description": "Riding a bicycle with hands on handlebars and alternating pedal motion.",
        "associated_objects": ["bicycle", "helmet", "handlebars"],
        "posture_cues": ["seated bent forward", "hands forward on bar", "legs angled at pedals"]
    },
    "dancing": {
        "index": 3,
        "name": "Dancing",
        "category": "Dynamic Movement",
        "severity": "info",
        "color": "#ec4899",  # Pink
        "icon": "sparkles",
        "description": "Expressive rhythmic body movements with extended limbs or dynamic poise.",
        "associated_objects": ["dance floor", "costume"],
        "posture_cues": ["extended arms", "kinetic leg stance", "body twist or leap"]
    },
    "drinking": {
        "index": 4,
        "name": "Drinking",
        "category": "Wellness & Sustenance",
        "severity": "wellness",
        "color": "#14b8a6",  # Teal
        "icon": "cup-soda",
        "description": "Lifting a cup, glass, mug, or bottle towards lips with tilted neck.",
        "associated_objects": ["water bottle", "coffee mug", "glass", "can"],
        "posture_cues": ["hand holding vessel to mouth", "head tilted back slightly", "elbow flexed"]
    },
    "eating": {
        "index": 5,
        "name": "Eating",
        "category": "Wellness & Sustenance",
        "severity": "wellness",
        "color": "#f97316",  # Orange
        "icon": "utensils",
        "description": "Bringing food or utensil to mouth, chewing, or seated with food plate.",
        "associated_objects": ["fork", "spoon", "plate", "food item", "chopsticks"],
        "posture_cues": ["hand to mouth with food", "seated near table surface"]
    },
    "fighting": {
        "index": 6,
        "name": "Fighting",
        "category": "Social & Security",
        "severity": "critical",
        "color": "#ef4444",  # Red Alert
        "icon": "shield-alert",
        "description": "Aggressive physical confrontation, punch, kick, grapple, or combat stance.",
        "associated_objects": ["multiple subjects"],
        "posture_cues": ["clenched fists", "aggressive forward lean", "grappling contact", "combative stance"]
    },
    "hugging": {
        "index": 7,
        "name": "Hugging",
        "category": "Social & Security",
        "severity": "info",
        "color": "#f43f5e",  # Rose
        "icon": "heart-handshake",
        "description": "Embracing another individual with arms wrapped around their upper body.",
        "associated_objects": ["multiple subjects"],
        "posture_cues": ["close proximity", "arms wrapped around torso/shoulders", "intertwined posture"]
    },
    "laughing": {
        "index": 8,
        "name": "Laughing",
        "category": "Wellness & Sustenance",
        "severity": "wellness",
        "color": "#eab308",  # Amber Yellow
        "icon": "smile",
        "description": "Expressive smiling/laughter with open mouth, head tilted back, joyful countenance.",
        "associated_objects": ["facial expression"],
        "posture_cues": ["open mouth smile", "creased eyes", "head thrown back or hand on chest"]
    },
    "listeningtomusic": {
        "index": 9,
        "name": "Listening to Music",
        "category": "Communication & Device",
        "severity": "normal",
        "color": "#8b5cf6",  # Violet
        "icon": "headphones",
        "description": "Wearing over-ear headphones or in-ear buds, often relaxed or tapping rhythm.",
        "associated_objects": ["headphones", "earbuds", "audio player"],
        "posture_cues": ["headwear over ears", "hands occasionally touching ear cups", "eyes closed or relaxed"]
    },
    "running": {
        "index": 10,
        "name": "Running",
        "category": "Dynamic Movement",
        "severity": "warning",  # In indoor spaces can signify emergency egress/panic
        "color": "#e11d48",  # Crimson
        "icon": "activity",
        "description": "Fast bipedal locomotion with flight phase, alternating wide leg stride and pumping arms.",
        "associated_objects": ["sportswear", "track"],
        "posture_cues": ["wide stride", "both feet off ground intermittently", "elbows bent 90 degrees pumping"]
    },
    "sitting": {
        "index": 11,
        "name": "Sitting",
        "category": "Productive & Desk",
        "severity": "normal",
        "color": "#64748b",  # Slate
        "icon": "armchair",
        "description": "Seated posture on chair, stool, couch, or floor with hips bent 90 degrees.",
        "associated_objects": ["chair", "sofa", "bench"],
        "posture_cues": ["thighs horizontal", "torso upright or leaning back", "stationary pose"]
    },
    "sleeping": {
        "index": 12,
        "name": "Sleeping",
        "category": "Wellness & Sustenance",
        "severity": "warning",  # In office/surveillance context
        "color": "#475569",  # Deep Slate
        "icon": "moon",
        "description": "Reclined, eyes closed, resting head on desk, couch, or bed in inert posture.",
        "associated_objects": ["bed", "pillow", "head on desk"],
        "posture_cues": ["horizontal posture or head down on arms", "eyes closed", "zero movement"]
    },
    "texting": {
        "index": 13,
        "name": "Texting",
        "category": "Communication & Device",
        "severity": "distraction",
        "color": "#f59e0b",  # Amber
        "icon": "message-square",
        "description": "Looking down with both or one hand holding smartphone at chest/waist level, typing.",
        "associated_objects": ["smartphone"],
        "posture_cues": ["neck flexed forward downward", "two thumbs or index finger on screen", "hands mid-torso"]
    },
    "using_laptop": {
        "index": 14,
        "name": "Using Laptop",
        "category": "Productive & Desk",
        "severity": "productive",
        "color": "#10b981",  # Emerald Green
        "icon": "laptop",
        "description": "Engaged with a laptop or keyboard with fingers on keys and gaze directed at display.",
        "associated_objects": ["laptop", "monitor", "keyboard", "mouse"],
        "posture_cues": ["hands forward on keyboard", "gaze level or slightly down at screen", "seated at desk"]
    }
}

def get_class_info(class_name: str) -> Dict[str, Any]:
    """Retrieve detailed metadata for any of the 15 classes."""
    norm_name = class_name.lower().replace(" ", "_")
    return CLASS_METADATA.get(norm_name, {
        "index": -1,
        "name": class_name,
        "category": "Unclassified",
        "severity": "normal",
        "color": "#94a3b8",
        "icon": "help-circle",
        "description": "Activity not indexed",
        "associated_objects": [],
        "posture_cues": []
    })
