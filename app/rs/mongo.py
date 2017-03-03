""""""


from app import mongo


import itertools
import numpy as np


class MongoRecommenderSystem(object):
    """MongoDB based recommender system."""

    def __init__(self):
        """"""
        self.build_statement_similarity()
        self.update_similarity()

    def get_matches(self, pid, sort_sim=None):
        """Get and return all matches for the given profile."""
        matches = []

        found = mongo.db.omrows.find({'pair': pid})
        if sort_sim is not None:
            found = mongo.db.omrows.find(
                {'pair': pid}).sort('similarity', sort_sim)

        for sim in found:
            matches.append(
                (list(set(list(sim['pair'])) - set([pid]))[0], sim['similarity']))

        return matches

    def add_reaction(self, rid):
        """Add a new reaction to the statement similarity matrix.
        Rows are only added if two or more users have reacted to the statment.
        """
        r = mongo.db.reactions.find_one({"_id": rid})
        rows = self.statement_rows(r['statement'], filter_by=r['profile'])
        mongo.db.smrows.insert_many(rows)

        return r['profile']

    def update_similarity(self, filter_by=None):
        """Update category and overall similarity matrices."""
        if mongo.db.smrows.count() == 0:
            self.build_statement_similarity()
            if mongo.db.smrows.count() == 0:
                return

        # Update category similarity.
        rows = []
        for c in mongo.db.categories.find():
            # Get unique profiles to generate possible combinations.
            profiles = set()
            for sim in mongo.db.smrows.find({'category': c['_id']}):
                [profiles.add(x) for x in sim['pair']]

            # Iterate over all possible combinations.
            for comb in itertools.combinations(profiles, 2):
                # If filtering, check that the filter object is contained
                # in the generatedd combination.
                if filter_by is not None and filter_by not in comb:
                    continue

                # Collect scores.
                scores = []
                for entry in mongo.db.smrows.find({'pair': {'$all':  list(comb)}}):
                    scores.append(
                        self.distance_score(c['weight'], entry['distance']))

                # Finally add a new row with the mean of the collected scores.
                rows.append({
                    'pair': list(comb),
                    'category': c['_id'],
                    'score': np.mean(scores)
                })

        # If the pairs for just a single profile is being updated then remove
        # all similarities for just that profile. Otherwise, remove all
        # similarities and rebuild.
        if filter_by is not None and mongo.db.cmrows.count() != 0:
            mongo.db.cmrows.remove({'pair': filter_by})
        else:
            mongo.db.cmrows.remove({})

        mongo.db.cmrows.insert_many(rows)

        # Update overall similarity.
        # Get unique profiles from category similarity matrix to generate
        # possible combinations for the overall similarity matrix.
        rows = []
        profiles = set()
        for sim in mongo.db.cmrows.find():
            [profiles.add(x) for x in sim['pair']]

        # Iterate over all possible combinations.
        for comb in itertools.combinations(profiles, 2):
            # If filtering, check that the filter object is contained
            # in the generatedd combination.
            if filter_by is not None and filter_by not in comb:
                continue

            # Collect category similarities.
            sims = []
            for entry in mongo.db.cmrows.find({'pair': {'$all':  list(comb)}}):
                sims.append(entry['score'])

            rows.append({
                'pair': list(comb),
                'similarity': np.sum(sims)
            })

        # If the pairs for just a single profile is being updated then remove
        # all similarities for just that profile. Otherwise, remove all
        # similarities and rebuild.
        if filter_by is not None and mongo.db.omrows.count() != 0:
            mongo.db.omrows.remove({'pair': filter_by})
        else:
            mongo.db.omrows.remove({})

        mongo.db.omrows.insert_many(rows)

    def build_statement_similarity(self):
        """Build the statement similarity matrix."""
        if mongo.db.smrows.count() > 0:
            return

        dst = self.distinct_reaction_statements()

        if len(dst) == 0:
            return

        rows = []
        for s in dst:
            rows = rows + self.statement_rows(s)

        mongo.db.smrows.remove({})
        mongo.db.smrows.insert_many(rows)

    def purge_similarity(self):
        """Purge all similarity matrices."""
        # Statement similarity.
        mongo.db.smrows.remove({})

        # Category similarity.
        mongo.db.cmrows.remove({})

        # Overall similarity.
        mongo.db.omrows.remove({})

    def clear_orphans(self, profile):
        """Remove orphaned similarities from all matrices."""
        # Statement similarity.
        mongo.db.smrows.remove({'pair': profile})

        # Category similarity.
        mongo.db.cmrows.remove({'pair': profile})

        # Overall similarity.
        mongo.db.omrows.remove({'pair': profile})

    def profiles(self):
        """Get all profiles in the datastore and return them as a list."""
        profile = mongo.db.profiles
        return [str(x) for x in profile.distinct("_id")]

    def statements(self):
        """Get all statements and return them in a list."""
        return [str(x) for x in mongo.db.statements.distinct("_id")]

    def statement_rows(self, statement, filter_by=None):
        rows = []
        cnt = mongo.db.reactions.find({'statement': statement}).count()
        if cnt == 1:
            return []

        cid = mongo.db.statements.find_one({'_id': statement})['category']
        profiles = mongo.db.reactions.find(
            {'statement': statement}).distinct('profile')
        for comb in itertools.combinations(profiles, 2):
            if filter_by is not None and filter_by not in comb:
                continue

            r0 = mongo.db.reactions.find_one(
                {'statement': statement, 'profile': comb[0]})['reaction']
            r1 = mongo.db.reactions.find_one(
                {'statement': statement, 'profile': comb[1]})['reaction']
            rows.append({
                'pair': list(comb),
                'statement': statement,
                'category': cid,
                'distance': abs(r0 - r1)
            })

        return rows

    def distinct_reaction_statements(self):
        """Get distinct statements from the reactions collection."""
        return mongo.db.reactions.find().distinct('statement')

    def distance_score(self, weight, distance):
        """Calculate the Euclidean distance score between two users based on
        the category weight."""
        return weight / (1 + distance)
