""""""


from app import mongo


import itertools
import numpy as np


class RecommenderSystem(object):
    """Spark based recommender system."""

    # SparkContext.
    spark_context = None

    # Statement Similarity Matrix.
    ssm = None

    # Category Similarity Matrix.
    csm = None

    # Overall Similarity Matrix.
    osm = None

    def __init__(self, spark_context):
        """"""

        # Initialize SparkContext.
        self.spark_context = spark_context

    def get_matches(self, pid):
        """Get and return all matches for the given profile."""
        m_rows = self.osm.filter(lambda row: pid in row[0])
        matches = []
        for row in m_rows.collect():
            matches.append(
                (list(set(list(row[0])) - set([pid]))[0], row[1]))

        return sorted(matches, key=lambda x: x[1], reverse=True)

    def distance_score(self, weight, distance):
        """Calculate the Euclidean distance score between two users based on
        the category weight."""
        return weight / (1 + distance)

    def load_data(self):
        dst = self.distinct_reaction_statements()
        rows = []
        for s in dst:
            rows = rows + self.statement_rows(s)

        self.ssm = self.spark_context.parallelize(rows)
        self.update_similarity()

    def add_reaction(self, rid):
        """Add a new reaction to the statement similarity matrix.
        Rows are only added if two or more users have reacted to the statment.
        """
        reaction = mongo.db.reactions
        r = reaction.find_one({"_id": rid})
        rows = self.statement_rows(r['statement'], filter_by=r['profile'])
        temp = self.spark_context.parallelize(rows)
        self.ssm = self.ssm.union(temp)
        return r['profile']

    def update_similarity(self, filter_by=None):
        """Update category and overall similarity matrices."""
        category = mongo.db.categories

        # Category similarity.
        rows = []
        for c in category.find():
            c_rows = self.ssm.filter(lambda row: row[2] == c['_id'])
            profiles = set()
            for row in c_rows.collect():
                [profiles.add(x) for x in row[0]]

            for comb in itertools.combinations(profiles, 2):
                if filter_by is not None and filter_by not in comb:
                    continue

                p_rows = c_rows.filter(
                    lambda p_row, comb=comb: comb[0] in p_row[0] and comb[1] in p_row[0])
                scores = []
                for entry in p_rows.collect():
                    scores.append(self.distance_score(c['weight'], entry[3]))
                rows.append((comb, c['_id'], np.mean(scores)))

        # Check this out in the future if any bottlenecks are noticed.
        # May need to manually unpersist the replaced RDD.
        if filter_by is not None and self.csm is not None:
            temp = self.csm.filter(lambda row: filter_by not in row[0])
            self.csm = temp.union(self.spark_context.parallelize(rows))
        else:
            self.csm = self.spark_context.parallelize(rows)

        # Overall similarity.
        rows = []
        profiles = set()
        for row in self.csm.collect():
            [profiles.add(x) for x in row[0]]

        for comb in itertools.combinations(profiles, 2):
            if filter_by is not None and filter_by not in comb:
                continue

            p_rows = self.csm.filter(
                lambda p_row, comb=comb: comb[0] in p_row[0] and comb[1] in p_row[0])
            sims = []
            for entry in p_rows.collect():
                sims.append(entry[2])

            rows.append((comb, np.sum(sims)))

        # Check this out in the future if any bottlenecks are noticed.
        # May need to manually unpersist the replaced RDD.
        if filter_by is not None and self.osm is not None:
            temp = self.osm.filter(lambda row: filter_by not in row[0])
            self.osm = temp.union(self.spark_context.parallelize(rows))
        else:
            self.osm = self.spark_context.parallelize(rows)

    def clear_orphans(self, profile):
        """Remove orphaned similarities from all matrices."""

        # Statement similarity.
        self.ssm = self.ssm.filter(
            lambda row, profile=profile: profile not in row[0])

        # Category similarity.
        self.csm = self.csm.filter(
            lambda row, profile=profile: profile not in row[0])

        # Overall similarity.
        self.osm = self.osm.filter(
            lambda row, profile=profile: profile not in row[0])

    def profiles(self):
        """Get all profiles in the datastore and return them as a list."""
        profile = mongo.db.profiles
        return [str(x) for x in profile.distinct("_id")]

    def statements(self):
        """Get all statements and return them in a list."""
        statement = mongo.db.statements
        return [str(x) for x in statement.distinct("_id")]

    def statement_rows(self, statement, filter_by=None):
        reaction = mongo.db.reactions
        rows = []
        cnt = reaction.find({"statement": statement}).count()
        if cnt == 1:
            return []

        cid = mongo.db.statements.find_one({"_id": statement})['category']
        profiles = reaction.find({"statement": statement}).distinct("profile")
        for c in itertools.combinations(profiles, 2):
            if filter_by is not None and filter_by not in c:
                continue

            r0 = reaction.find_one(
                {"statement": statement, "profile": c[0]})['reaction']
            r1 = reaction.find_one(
                {"statement": statement, "profile": c[1]})['reaction']
            rows.append((c, statement, cid, abs(r0 - r1)))

        return rows

    def distinct_reaction_statements(self):
        """Get distinct statements from the reactions collection."""
        reaction = mongo.db.reactions
        return reaction.find().distinct('statement')
