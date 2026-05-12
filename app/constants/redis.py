
class GRedisGlobalConstant:
    GRAXON_PREFIX = "graxon"
    TEMP = "temp"


class GRedisTagsConstants:
    TAGS_PREFIX = "tags"


class GRedisKeys:
    TAG_TEMP_KEY = f"{GRedisGlobalConstant.GRAXON_PREFIX}:{GRedisGlobalConstant.TEMP}:{GRedisTagsConstants.TAGS_PREFIX}"
    TAG_KEY = f"{GRedisGlobalConstant.GRAXON_PREFIX}:{GRedisTagsConstants.TAGS_PREFIX}"
