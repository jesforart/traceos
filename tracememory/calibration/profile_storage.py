from typing import List, Dict, Optional
from .models import ArtistProfile
import json

class ProfileStorage:
    """Store and retrieve artist profiles."""

    def __init__(self):
        self.profiles: Dict[str, ArtistProfile] = {}

    def store_profile(self, profile: ArtistProfile):
        """Store artist profile."""
        self.profiles[profile.id] = profile

    def get_profile(self, profile_id: str) -> Optional[ArtistProfile]:
        """Get profile by ID."""
        return self.profiles.get(profile_id)

    def get_all_profiles(self) -> List[ArtistProfile]:
        """Get all profiles."""
        return list(self.profiles.values())

    def delete_profile(self, profile_id: str):
        """Delete profile."""
        if profile_id in self.profiles:
            del self.profiles[profile_id]

    def export_to_json(self, profile_id: str) -> Optional[str]:
        """Export profile as JSON string."""
        profile = self.get_profile(profile_id)
        if not profile:
            return None

        return profile.json(indent=2)

    def import_from_json(self, json_str: str) -> ArtistProfile:
        """Import profile from JSON string."""
        profile = ArtistProfile.parse_raw(json_str)
        self.store_profile(profile)
        return profile
