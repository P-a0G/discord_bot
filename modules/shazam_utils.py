import asyncio

from shazamio import Shazam


class ShazamUtils:
    def __init__(self):
        self.shazam = Shazam()

    async def search_song(self, filename: str):
        try:
            out = await self.shazam.recognize(filename)

            print(out)
            print("This sound is:", out["track"]["title"], out["track"]["subtitle"])
            metadata_dict = {meta["title"]: meta["text"] for meta in out["track"]["sections"][0]["metadata"]}
            print("Metadata:\n", metadata_dict)

            return {
                "title": out["track"]["title"],
                "author": out["track"]["subtitle"],
            }

        except Exception as e:
            print(f"Error searching for song: {filename} error: {e}")
            return {}


if __name__ == '__main__':
    shazam_utils = ShazamUtils()
    loop = asyncio.get_event_loop()

    print("Trying to search for song in file './musics/sample.mp3'...")
    try:
        result = loop.run_until_complete(shazam_utils.search_song("./musics/sample.mp3"))
    except Exception as e:
        result = {"error": str(e)}
    print(result)
