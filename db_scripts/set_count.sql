UPDATE Words SET GovernorCount = (SELECT SUM(D.Count) FROM DependencyRelations as D WHERE D.GovernorID = WID);
UPDATE Words SET DepCount = (SELECT SUM(D.Count) FROM DependencyRelations as D WHERE D.DependentID = WID);
